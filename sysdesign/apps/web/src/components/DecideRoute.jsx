export const decideRoute = (user) => {
  if (user?.role === "USER") {
    return "/user-dashboard";
  }

  if (user?.role === "PRODUCT_OWNER") {
    return "/project-dashboard";
  }

  if (user?.role === "CLIENT") {
    return "/client-dashboard";
  }

  return "/";
};