import { useRef, useState } from "react";
import axios from "axios";

export default function useClientSearch() {
  const timerRef = useRef(null);
  const abortRef = useRef(null);
  const cacheRef = useRef(new Map());

  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchClients = (value) => {
    const query = value.trim();

    // Cancel pending debounce
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Cancel previous API request
    if (abortRef.current) {
      abortRef.current.abort();
    }

    if (query.length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }

    // Return cached result
    if (cacheRef.current.has(query.toLowerCase())) {
      setResults(cacheRef.current.get(query.toLowerCase()));
      setLoading(false);
      return;
    }

    setLoading(true);

    timerRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await axios.get(
          "http://127.0.0.1:8000/users/search",
          {
            params: {
              q: query,
            },
            signal: controller.signal,
          }
        );

        console.log("search results", response);

        const users = response.data;

        cacheRef.current.set(query.toLowerCase(), users);

        setResults(users);
      } catch (error) {
        if (error.name === "CanceledError") {
          return;
        }

        if (error.name === "AbortError") {
          return;
        }

        console.error("Client search failed:", error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 350);
  };

  return {
    searchClients,
    results,
    loading,
  };
}