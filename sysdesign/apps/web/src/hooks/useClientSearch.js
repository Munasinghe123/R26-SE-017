import { useRef, useState, useEffect, useCallback } from "react";
import axios from "axios";

export default function useClientSearch() {
  const timerRef = useRef(null);
  const abortRef = useRef(null);
  const cacheRef = useRef(new Map());

  const [results, setResults] = useState([]);
  const [defaultClients, setDefaultClients] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch initial clients on mount
  const loadDefaultClients = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get("/users/search", { params: { q: "" } });
      const clients = response.data || [];
      setDefaultClients(clients);
      setResults(clients);
      cacheRef.current.set("", clients);
    } catch (error) {
      console.error("Failed to load initial clients:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDefaultClients();
  }, [loadDefaultClients]);

  const searchClients = (value) => {
    const query = (value || "").trim();

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    if (abortRef.current) {
      abortRef.current.abort();
    }

    // If query is empty, show default clients
    if (!query) {
      setResults(defaultClients);
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
        const response = await axios.get("/users/search", {
          params: { q: query },
          signal: controller.signal,
        });

        const users = response.data || [];
        cacheRef.current.set(query.toLowerCase(), users);
        setResults(users);
      } catch (error) {
        if (error.name === "CanceledError" || error.name === "AbortError") {
          return;
        }
        console.error("Client search failed:", error);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
  };

  return {
    searchClients,
    results,
    loading,
    reloadClients: loadDefaultClients,
  };
}