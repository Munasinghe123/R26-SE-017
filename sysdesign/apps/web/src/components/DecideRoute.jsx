export const decideRoute = (user) => {
  if (user?.role === "USER") {
    return "/user-dashboard";
  }

  if (
    user?.role === "PRODUCT_OWNER" ||
    user?.role === "CLIENT"
  ) {
    return "/project-dashboard";
  }

  return "/";
};