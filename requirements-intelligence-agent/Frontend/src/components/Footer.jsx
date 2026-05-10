import React from "react";
import Logo from "../Images/logo.png";

import { Link } from "react-router-dom";

function Footer() {
  return (
    <footer className="relative w-full  text-gray-400">

      {/* Main footer */}
      <div className="w-full px-20 lg:px-30 py-10 flex flex-col lg:flex-row items-center justify-between gap-8">

        {/* Brand */}
        <Link to="/" className="flex items-center gap-2">
          <div className="w-32 h-32  rounded-2xl flex items-center justify-center ">
            <img src={Logo} className="h-32 w-32 object-contain rounded-2xl" />
          </div>
        
        </Link>

        {/* Links */}
        <div className="flex items-center gap-8 text-sm">
          <span className="text-white/80 hover:text-white transition cursor-pointer">
            About
          </span>

          <span className="text-white/80 hover:text-white transition cursor-pointer">
            Contact
          </span>

          <span className="text-white/80 hover:text-white transition cursor-pointer">
            Features
          </span>

          <span className="text-white/80 hover:text-white transition cursor-pointer">
            Examples
          </span>

          <span className="text-white/80 hover:text-white transition cursor-pointer">
            Pricing
          </span>
        </div>

        {/* Socials */}
        {/* <div className="flex gap-3">
          <a className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center hover:bg-orange-500 hover:text-white transition">
            <Instagram className="w-4 h-4" />
          </a>
          <a className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center hover:bg-orange-500 hover:text-white transition">
            <Twitter className="w-4 h-4" />
          </a>
          <a className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center hover:bg-orange-500 hover:text-white transition">
            <Facebook className="w-4 h-4" />
          </a>
        </div> */}

      </div>

      {/* Bottom */}
      <div className="border-t border-white/10 py-4 text-center text-xs text-white">
        © 2026 SystemDesign. All rights reserved.
      </div>

    </footer>
  );
}

export default Footer;