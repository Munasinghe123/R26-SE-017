import React, { useEffect, useState } from "react";
import Logo from "../Images/logo.png";
import { UserRound } from "lucide-react";
import { Link } from "react-router-dom";

function Header() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div
      className={`fixed top-0 left-0 w-full 
              flex items-center justify-between
              px-6 lg:px-30 z-20 py-2
              transition-colors duration-300
              ${scrolled ? "bg-black/30 backdrop-blur-md" : "bg-transparent"}`}
    >
      <Link to="/">
        <img
          src={Logo}
          className="h-10 w-10 lg:h-10 lg:w-20 object-contain cursor-pointer"
          alt="logo"
        />
      </Link>

      <div className="flex items-center gap-6 lg:gap-20 px-6 py-2 ">
        <span className="text-white hover:text-cyan-300  transition cursor-pointer">
          About
        </span>
        <span className="text-white hover:text-cyan-300 transition cursor-pointer">
          Contact
        </span>
        <span className="text-white hover:text-cyan-300 transition cursor-pointer">
          Features
        </span>
        <span className="text-white hover:text-cyan-300 transition cursor-pointer">
          Examples
        </span>
        <Link to="/get-started">
          <button
            className="flex items-center gap-3 cursor-pointer
          inset-0 bg-gradient-to-r from-cyan-400/0 via-cyan-400/30 to-purple-500/0
                    relative px-5 py-2 
                    text-sm font-medium uppercase tracking-[2px]
                    text-white rounded-full
                    border border-cyan-400/60
                    bg-white/5 backdrop-blur-md
                    overflow-hidden
                    transition-all duration-300
                    hover:border-cyan-200
                    hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"
          >
            <UserRound size={16} strokeWidth={2} />
            <span className="relative z-10">Sign In</span>
          </button>
        </Link>
      </div>
    </div>
  );
}

export default Header;