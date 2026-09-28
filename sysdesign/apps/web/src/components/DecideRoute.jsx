// export const decideRoute = (user) => {
//   if (user?.role === "USER") {
//     return "/user";
//   }

//   if (user?.role === "PRODUCT_OWNER") {
//     return "/project-dashboard";
//   }

//   if (user?.role === "CLIENT") {
//     return "/client-dashboard";
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