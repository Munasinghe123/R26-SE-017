import { configureStore } from "@reduxjs/toolkit";
import userReducer from "../Redux/UserSlice";
import projectReducer from "../Redux/ProjectSlice";

import {
  persistStore,
  persistReducer,
} from "redux-persist";
import storage from "redux-persist/lib/storage";

const persistConfig = {
  key: "root",
  storage,
};

const persistedUserReducer = persistReducer(
  persistConfig,
  userReducer
);

export const store = configureStore({
  reducer: {
    user: persistedUserReducer,
    project: projectReducer,
  },

  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          "persist/PERSIST",
          "persist/REHYDRATE",
        ],
      },
    }),
});

export const persistor = persistStore(store);