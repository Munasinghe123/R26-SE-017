import React from "react";

const FloatingInput = ({
  label,
  type = "text",
  icon: Icon,
  value,
  onChange,
}) => {
  return (
    <div className="relative w-full">
      {/* Input */}
      <input
        type={type}
        value={value}
        onChange={onChange}
        required
        className="
          peer w-full pl-10 pr-4 py-3 bg-transparent border border-cyan-300
          text-white rounded-md
          focus:outline-none focus:ring-1 focus:ring-cyan-400
        "
      />

      {/* Icon */}
      {Icon && (
        <Icon className="absolute left-3 top-3.5 text-white peer-focus:text-cyan-400 w-5 h-5 pointer-events-none" />
      )}

      {/* Floating Label */}
      <label
        className="
          absolute left-10 top-3 text-white pointer-events-none
          transition-all duration-200
          peer-focus:-top-3 peer-focus:text-sm peer-focus:text-cyan-400
          peer-valid:-top-3 peer-valid:text-sm peer-valid:text-cyan-400
        "
      >
        {label}
      </label>
    </div>
  );
};

export default FloatingInput;
