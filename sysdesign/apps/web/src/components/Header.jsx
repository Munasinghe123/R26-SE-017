import React, { useEffect, useState } from "react";
import Logo from "../Images/logo.png";
import { UserRound, LogOut } from "lucide-react";
import { Link } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { logout } from "../Redux/UserSlice";

function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const dispatch = useDispatch();

  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);
  const user = useSelector((state) => state.user.userInfo);

  console.log("Header - isAuthenticated:", isAuthenticated);
  console.log("Header - user:", user);
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleLogout = () => {
    dispatch(logout());
    setProfileOpen(false);
  };

  return (
    <div
      className={`fixed top-0 left-0 w-full
        flex items-center justify-between
        px-6 lg:px-30 z-20 py-2
        transition-colors duration-300
        ${scrolled ? "bg-black/30 backdrop-blur-md" : "bg-transparent"}`}
    >
      {/* Logo */}
      <Link to="/">
        <img
          src={Logo}
          className="h-10 w-10 lg:h-10 lg:w-20 object-contain cursor-pointer"
          alt="logo"
        />
      </Link>

      {!isAuthenticated ? (
        /* ---------------- UNAUTHENTICATED ---------------- */
        <div className="flex items-center gap-6 lg:gap-20 px-6 py-2">
          <span className="text-white hover:text-cyan-300 transition cursor-pointer">
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
        </div>
      ) : (
        /* ---------------- AUTHENTICATED ---------------- */
        <div className="relative flex items-center gap-4">
          {/* User name */}
          <div className="flex gap-1.5">
            <span className="text-white font-medium"> Hi,</span>
            <span className="text-white font-medium">
              {user?.name || "User"} !
            </span>
          </div>

          {/* Profile button */}
         
            <button
              onClick={() => setProfileOpen((prev) => !prev)}
              className="flex items-center justify-center
              h-10 w-10
              rounded-full
              border border-cyan-400/60
              bg-white/5 backdrop-blur-md
              text-white
              cursor-pointer
              transition-all duration-300
              hover:border-cyan-200
              hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"
            >
              <UserRound size={18} />
            </button>
         

          {/* Profile dropdown */}
          {profileOpen && (
            <div
              className="absolute right-0 top-14
                w-44
                rounded-xl
                border border-white/10
                bg-black/80
                backdrop-blur-xl
                p-2
                shadow-xl"
            >
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3
                  rounded-lg
                  px-3 py-2
                  text-sm text-white
                  transition
                  hover:bg-white/10
                  hover:text-red-400
                  cursor-pointer"
              >
                <LogOut size={16} />

                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Header;
