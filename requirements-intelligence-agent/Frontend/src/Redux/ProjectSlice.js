import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  currentProject: null,
};

const projectSlice = createSlice({
  name: "project",
  initialState,
  reducers: {
    setCurrentProject: (state, action) => {
      console.log("SET CURRENT PROJECT REDUCER HIT");
      console.log("PAYLOAD:", action.payload);

      state.currentProject = action.payload;

      console.log("STATE AFTER UPDATE:", state);
    },

    clearCurrentProject: (state) => {
      state.currentProject = null;
    },
  },
});

export const { setCurrentProject, clearCurrentProject } = projectSlice.actions;

export default projectSlice.reducer;
