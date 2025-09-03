"""
HDX MCP Server - HDX Tools Usage Instructions Prompt.

This module contains the HDX tools usage instructions prompt that helps users
understand how to effectively use HDX tools and handle large datasets.
"""


async def hdx_usage_instructions() -> str:
    """
    Instructions for using HDX tools effectively.

    Provides guidance on handling disaggregated data, pagination, and parameter usage.

    Returns:
        Formatted instructions for HDX tool usage
    """
    return """# Instructions for using HDX Tools

## Understanding HDX Data Structure

HDX tools provide access to highly disaggregated humanitarian data. This means "
"data is broken down by multiple dimensions such as:
- **Geographic levels**: Country, admin1 (states/provinces), admin2 (districts/counties)
- **Demographics**: Age ranges, gender, population groups
- **Time periods**: Monthly, quarterly, or yearly data points
- **Data sources**: Different organizations and methodologies

## Critical: Data Coverage and Administrative Level Aggregation

**CRITICAL WARNING**: Data coverage is only determined by the
`metadata_data_availability_get` tool. Just because a country is in the system
doesn't mean it has data. Always verify data availability before making data queries.

**IMPORTANT**: Data availability varies by country and administrative level.
Some countries have data only at admin level 0 (country), others at admin level 1
(states/provinces), and some at admin level 2 (districts/counties).

### Before Making ANY Data Queries
1. **ALWAYS check data coverage first** using `metadata_data_availability_get`
   for the target country
2. **Verify that data actually exists** - presence in location metadata doesn't
   guarantee data availability
3. **Identify the lowest available admin level** for the country
   (0 = country, 1 = state, 2 = district)
4. **Query at the lowest available level** to avoid excessive data retrieval

### Example: Getting Total Population for Country X
```
1. Check availability:
   → metadata_data_availability_get (location_code="AFG")

2. If country has data at admin level 1:
   → Use admin level 1 queries to get state-level data, then aggregate

3. If country only has admin level 0:
   → Use country-level queries directly

4. NEVER query admin level 2 if admin level 0 or 1 is sufficient
```

### Why This Matters
- **Efficiency**: Prevents downloading unnecessary granular data
- **Performance**: Reduces API response times and data processing
- **Accuracy**: Ensures you're getting the most appropriate data level
- **Resource optimization**: Avoids overwhelming the API with massive datasets

**Rule of thumb**: For aggregate questions (totals, country-wide statistics),
always use the highest administrative level (lowest number) that has data available.

## Universal Pagination Support

**🔄 IMPORTANT: You can page through results using `limit` and `offset`
parameters on ALL HDX tools.**

### Default Behavior
- Most HDX tools return data with a **default limit of 10 records**
- This may only show a small subset of available data
- The API can return hundreds or thousands of records for comprehensive
  datasets
- **All tools support pagination** - use `limit` and `offset` to access complete
  datasets

### Strategies for Getting Complete Data

#### 1. Check if Parameters Accept 'all'
Some parameters (like `age_range`, `gender`, `population_group`) accept
`'all'` as a value:
```
age_range: 'all'
gender: 'all'
population_group: 'all'
```
Use these when you want data across all categories.

#### 2. Increase the Limit Parameter
If parameters don't accept `'all'`, increase the `limit` parameter:
- **Start with limit=100** (maximum recommended for single requests)
- This will give you up to 100 records instead of the default 10

#### 3. Use Pagination for Large Datasets
**ALL HDX tools support pagination using `limit` and `offset` parameters**:
- **limit**: Number of records per page (default 10, maximum 100)
- **offset**: Start position (0 for first page, 100 for second page, etc.)

**Standard pagination pattern**:
1. First call: `limit=100, offset=0` (records 1-100)
2. Second call: `limit=100, offset=100` (records 101-200)
3. Third call: `limit=100, offset=200` (records 201-300)
4. Continue until you get fewer than 100 records (indicating last page)

**You can page through results using limit and offset for any HDX tool.**

#### 4. Be Specific When Possible
Instead of retrieving all data, consider asking users to be more specific:
- **Geographic focus**: "Which specific country or region?"
- **Time period**: "What year or date range?"
- **Population type**: "Which population group (refugees, IDPs, returnees)?"
- **Demographic focus**: "Which age groups or gender?"

## Best Practices

### Start Broad, Then Narrow
1. **Explore available options** using metadata tools:
   - `metadata_location_get` for countries/regions
   - `metadata_admin1_get` for states/provinces
   - `metadata_admin2_get` for districts/counties

2. **Check data availability** before detailed queries:
   - `metadata_data_availability_get` shows what data exists for specific locations/years
   - **CRITICAL**: Identify the lowest admin level available for efficient aggregation

3. **Make targeted requests** based on exploration results

### Optimize Your Queries
- **Use specific location codes** instead of broad geographic areas
- **Filter by relevant time periods** rather than requesting all historical data
- **Choose appropriate administrative levels** (country vs. state vs. district)
- **Select relevant population groups** rather than requesting all groups

### Handle Results Efficiently
- **Check the total count** in responses to understand dataset size
- **Use meaningful limits** - don't request more data than needed
- **Consider data processing time** - larger datasets take longer to process

### ⚠️ CRITICAL: Never Manually Aggregate Data

**IMPORTANT: Never sum data yourself, only take the data verbatum
from the tool. If you do not have data at the correct aggregate
level, inform the user.**

**NEVER aggregate totals yourself to answer a question if you do not have the values "
"already aggregated from the tool.**

- **Do NOT** sum up individual records to create totals
- **Do NOT** manually calculate country-wide statistics from subnational data
- **Do NOT** aggregate across time periods, demographics, or geographic areas yourself
- **If data is not pre-aggregated**, inform the user that aggregate data is not available
- **Always use** the most appropriate administrative level that has pre-aggregated data
- **Example**: If asking for total refugees in a country, use country-level data if "
"available, don't sum state-level data

## Example Workflow

```
1. Explore locations:
   → metadata_location_get (limit=100)

2. Check data coverage and admin levels (MANDATORY):
   → metadata_data_availability_get (location_code="AFG", limit=100)
   (Note: Verify data actually exists, then check which admin levels have data
   - use the lowest available)

3. Get specific data at appropriate admin level:
   → affected_people_idps_get (location_code="AFG", admin_level=0, limit=100)
   (Use admin_level=0 if available, otherwise 1 or 2)

4. If more data needed:
   → affected_people_idps_get (location_code="AFG", admin_level=0, limit=100, offset=100)
```

## When to Ask for Specificity

If a query would return a very large dataset, consider asking users:
- "Would you like data for a specific country or region?"
- "What time period are you most interested in?"
- "Are you looking for a particular population group or demographic?"
- "Do you need subnational (state/district) level detail?"

This approach provides more relevant results while being more efficient with API resources.
"""
