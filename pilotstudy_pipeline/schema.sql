CREATE SCHEMA IF NOT EXISTS "public";
DROP TABLE IF EXISTS "public"."button_type" CASCADE;
DROP TABLE IF EXISTS "public"."exhibition" CASCADE;
DROP TABLE IF EXISTS "public"."visitor_interactions" CASCADE;

CREATE TABLE "public"."button_type" (
    "val" INT,
    "type" INT,
    "description" TEXT,
    "button_id" INT NOT NULL,
    PRIMARY KEY ("button_id")
);

CREATE TABLE "public"."exhibition" (
    "id" INT NOT NULL,
    "name" TEXT NOT NULL,
    "floor" INT NOT NULL,
    "department" TEXT NOT NULL,
    "start_date" DATE NOT NULL,
    "description" TEXT,
    PRIMARY KEY ("id")
);

CREATE TABLE "public"."visitor_interactions" (
    "site" INT NOT NULL,
    "at" TIMESTAMP NOT NULL,
    "button_id" INT NOT NULL,
    "interaction_id" SERIAL PRIMARY KEY,
    FOREIGN KEY (site) REFERENCES exhibition(id),
    FOREIGN KEY (button_id) REFERENCES button_type(button_id)
);

-- Foreign key constraints
-- Schema: public
ALTER TABLE "public"."visitor_interactions" ADD CONSTRAINT "fk_visitor_interactions_site_exhibition_id" FOREIGN KEY("site") REFERENCES "public"."exhibition"("id");
ALTER TABLE "public"."visitor_interactions" ADD CONSTRAINT "fk_visitor_interactions_button_id_button_type_button_id" FOREIGN KEY("button_id") REFERENCES "public"."button_type"("button_id");

-- Add Master data to button_type table
INSERT INTO button_type (button_id, val, type, description)
    VALUES
        (0, -1, 0, 'Assistance'),
        (1, -1, 1, 'Emergency'),
        (2, 0, NULL, 'Terrible'),
        (3, 1, NULL, 'Bad'),
        (4, 2, NULL, 'Neutral'),
        (5, 3, NULL, 'Good'),
        (6, 4, NULL, 'Amazing')
    ON CONFLICT DO NOTHING;