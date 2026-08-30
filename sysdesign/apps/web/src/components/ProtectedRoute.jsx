import React from "react";
import { Navigate } from "react-router-dom";
import { useSelector } from "react-redux";

function ProtectedRoute({ children }) {
  const isAuthenticated = useSelector(
    (state) => state.user.isAuthenticated
  );

  if (!isAuthenticated) {
    return <Navigate to="/get-started" replace />;
  }

  return children;
}

export default ProtectedRoute;