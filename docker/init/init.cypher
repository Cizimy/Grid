// Constraints (Ensure uniqueness for primary keys)
CREATE CONSTRAINT constraint_user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userID IS UNIQUE;
CREATE CONSTRAINT constraint_session_id IF NOT EXISTS FOR (s:GenerationSession) REQUIRE s.sessionID IS UNIQUE;
CREATE CONSTRAINT constraint_image_id IF NOT EXISTS FOR (i:GeneratedImage) REQUIRE i.imageID IS UNIQUE;
CREATE CONSTRAINT constraint_vibe_id IF NOT EXISTS FOR (v:VibeImage) REQUIRE v.vibeID IS UNIQUE;
CREATE CONSTRAINT constraint_template_id IF NOT EXISTS FOR (t:PromptTemplate) REQUIRE t.templateID IS UNIQUE;
CREATE CONSTRAINT constraint_set_id IF NOT EXISTS FOR (p:ParameterSet) REQUIRE p.setID IS UNIQUE;
CREATE CONSTRAINT constraint_tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.tagName IS UNIQUE;
CREATE CONSTRAINT constraint_model_name IF NOT EXISTS FOR (m:AiModel) REQUIRE m.modelName IS UNIQUE;

// Indexes (Improve query performance)
CREATE INDEX index_tag_name IF NOT EXISTS FOR (t:Tag) ON (t.tagName);
CREATE INDEX index_session_timestamp IF NOT EXISTS FOR (s:GenerationSession) ON (s.timestamp); // Recommended
CREATE INDEX index_image_rating IF NOT EXISTS FOR (i:GeneratedImage) ON (i.rating); // Recommended
CREATE INDEX index_image_status IF NOT EXISTS FOR (i:GeneratedImage) ON (i.generationStatus); // Recommended for filtering by status

// Note: Consider adding indexes on other frequently queried properties as needed.

// (任意) 開発用初期データ (例: デフォルトUserノード作成)
MERGE (u:User {userID: "default"}) ON CREATE SET u.username = "Default User", u.createdAt = datetime();