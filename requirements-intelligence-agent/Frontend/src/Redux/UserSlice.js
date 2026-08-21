import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  userInfo: null,
  isAuthenticated: false,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    loginSuccess: (state, action) => {
      state.userInfo = action.payload.user;
      state.isAuthenticated = true;
    },

    updateUser: (state, action) => {
      state.userInfo = action.payload;
    },

    logout: (state) => {
      state.userInfo = null;
      state.isAuthenticated = false;
    },
  },
});

export const { loginSuccess,updateUser, logout } = userSlice.actions;
export default userSlice.reducer;