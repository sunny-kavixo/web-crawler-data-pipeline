-- Crawl health and content analytics
SELECT status_code, COUNT(*) AS pages
FROM pages GROUP BY status_code ORDER BY pages DESC;

SELECT date_trunc('day', fetched_at) AS day, COUNT(*) AS pages
FROM pages GROUP BY 1 ORDER BY 1 DESC;

SELECT content_hash, COUNT(*) AS duplicates
FROM pages
WHERE content_hash IS NOT NULL
GROUP BY content_hash HAVING COUNT(*) > 1
ORDER BY duplicates DESC;

SELECT url, char_length(body_text) AS text_chars
FROM pages WHERE error IS NULL
ORDER BY text_chars DESC LIMIT 20;
