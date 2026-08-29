-- Safe schema adjustment for existing Neon/PostgreSQL deployments.
-- This migration keeps the table and data intact while renaming the legacy image path column.

ALTER TABLE diagrams
    RENAME COLUMN diagram_image_path TO cloudinary_url;

-- If the column is already renamed in a later deployment, this statement is a no-op.
-- ALTER TABLE IF EXISTS diagrams RENAME COLUMN diagram_image_path TO cloudinary_url;
