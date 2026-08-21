// export const decideRoute = (user) => {
//   if (user?.role === "USER") {
//     return "/welcome";
//   }

//   if (
//     user?.role === "PRODUCT_OWNER" ||
//     user?.role === "CLIENT"
//   ) {
//     return "/project-dashboard";
//   }

//   return "/";
// };

export const decideRoute = (user) => {
  if (
    user?.role === "USER" ||
    user?.role === "PRODUCT_OWNER" ||
    user?.role === "CLIENT"
  ) {
    return "/project-dashboard";
  }

  return "/";
};