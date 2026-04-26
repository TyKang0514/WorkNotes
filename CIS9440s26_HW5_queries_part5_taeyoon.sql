WITH restaurant_counts AS (
  SELECT
       l.zip_code AS zip_code,
       l.borough AS borough,
       COUNT(*) AS total_restaurants,
  FROM `ta26s_COPY_HW_warehouse_CIS9440_for_HW5.fact_restaurant_applications` f
    INNER JOIN `ta26s_COPY_HW_warehouse_CIS9440_for_HW5.dim_location` l
        ON f.location_key = l.location_key
  GROUP BY l.zip_code, l.borough
   ),

restaurant_count_tiers_by_zip AS (
-- add in the full select statement from part 3 as the content of this CTE
  SELECT
   *,
   CASE
    WHEN total_restaurants >= 200 THEN 'very high'
    WHEN total_restaurants >= 150 THEN 'high'
    WHEN total_restaurants > 50 THEN 'medium'
    ELSE 'low_or_typical'
   END AS restaurant_density_tier
  FROM restaurant_counts
),

complaint_counts_by_zip AS (
-- what should go in here? HINT: a query you have already written
SELECT
  l.zip_code AS zip_code,
  l.borough AS borough,
  COUNT(*) AS total_complaints,
FROM `ta26s_COPY_HW_warehouse_CIS9440_for_HW5.fact_dot_311_requests` f 
INNER JOIN `ta26s_COPY_HW_warehouse_CIS9440_for_HW5.dim_location` l
  ON f.location_key = l.location_key 
GROUP BY l.zip_code, l.borough
ORDER BY total_complaints DESC
)

SELECT
  ccz.zip_code,
  ccz.borough,
  rz.total_restaurants,
  ccz.total_complaints,
  rz.restaurant_density_tier,
  ROUND(ccz.total_complaints / rz.total_restaurants,2) AS complaints_per_restaurant
--see below instructions for what to select
FROM complaint_counts_by_zip ccz
INNER JOIN restaurant_count_tiers_by_zip rz
    ON ccz.zip_code = rz.zip_code AND ccz.borough = rz.borough
WHERE restaurant_density_tier="very high"
--?? anything else? WHERE..? GROUP BY? ORDER BY?
