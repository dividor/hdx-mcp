"""
HDX MCP Server - Data Coverage Guidance Prompt

This module contains specific guidance for understanding and checking data coverage
across different countries, administrative levels, and data types in HDX.
"""


async def data_coverage_guidance() -> str:
    """
    Instructions for understanding and checking data coverage in HDX.

    Provides critical guidance on data availability verification and administrative
    level coverage patterns across different countries.

    Returns:
        Formatted instructions for data coverage verification
    """
    return """# HDX Data Coverage Guidance

## Critical Understanding: Data Coverage is NOT Universal

**⚠️ ESSENTIAL RULE**: Just because a country is listed in location or admin
metadata doesn't mean it has actual data in HDX. You MUST use the
`metadata_data_availability_get` tool to confirm data availability.

## How Data Coverage Works

### Administrative Level Variations
Data coverage varies significantly by administrative level for each country:

- **Admin Level 0 (Country)**: National-level data
- **Admin Level 1 (States/Provinces)**: Subnational first-level divisions
- **Admin Level 2 (Districts/Counties)**: Subnational second-level divisions

### Coverage Patterns by Country
Different countries have different coverage patterns:

#### Pattern 1: Country-Level Only (Admin 0)
- Some countries only have national-level aggregated data
- No subnational breakdown available
- Example: Total population for entire country

#### Pattern 2: State/Province Level (Admin 0 + Admin 1)
- Countries with state or province-level data
- More granular than national but not district-level
- Example: Population by state/province

#### Pattern 3: Full Coverage (Admin 0 + Admin 1 + Admin 2)
- Countries with complete administrative hierarchy
- Data available at country, state, and district levels
- Most granular data available

#### Pattern 4: Partial Coverage
- Countries may have data for some admin levels but not others
- Coverage may vary by data type (population vs. refugees vs. food security)
- Some regions within a country may have data while others don't

## Data Type Variations

Coverage also varies by data type within the same country:

### Common Scenarios
- **Population data**: Available at admin 0 and 1
- **Refugee data**: Only available at admin 0
- **Food security**: Available at admin 2
- **Conflict events**: Available at admin 1 and 2

## MANDATORY Verification Process

### Step 1: Never Assume Data Exists
- Location metadata shows geographic entities that CAN have data
- It does NOT guarantee that data actually exists
- Always verify before making data queries

### Step 2: Use metadata_data_availability_get
```
Before ANY data query:
→ metadata_data_availability_get(location_code="XXX")

This will show:
- Which data types are available
- Which administrative levels have data
- Which time periods are covered
- Which population groups are included
```

### Step 3: Check Coverage for Your Specific Need
When the availability check returns results, verify:
- ✅ **Data type exists**: Is the data you need actually available?
- ✅ **Admin level exists**: Is data available at the level you need?
- ✅ **Time period covered**: Is data available for your time frame?
- ✅ **Population coverage**: Is data available for your target population?

### Step 4: Adapt Your Query Strategy
Based on availability results:
- **If admin 2 data exists**: Use it for most granular results
- **If only admin 1 exists**: Query at state/province level
- **If only admin 0 exists**: Use country-level data
- **If no data exists**: Inform user that data is not available

## Example Verification Workflow

```
User asks: "What's the refugee population in Somalia?"

Step 1: Check data availability
→ metadata_data_availability_get(location_code="SOM")

Step 2: Review results to see:
- Does Somalia have refugee data? ✓
- At which admin levels? (e.g., admin 0 and 1)
- For which time periods? (e.g., 2020-2024)
- For which population groups? (e.g., refugees, IDPs)

Step 3: Query at appropriate level
→ affected_people_refugees_get(location_code="SOM", admin_level=1)

Step 4: If no data found, inform user:
"Somalia does not have refugee data available in HDX. Available data types "
"are: [list from availability check]"
```

## Common Mistakes to Avoid

### ❌ Wrong Approach
1. See "Somalia" in location metadata
2. Immediately query: `affected_people_refugees_get(location_code="SOM")`
3. Get empty results or errors
4. Assume there's no data anywhere

### ✅ Correct Approach
1. See "Somalia" in location metadata
2. First check: `metadata_data_availability_get(location_code="SOM")`
3. Review what data actually exists
4. Query only for data types and levels that are confirmed available
5. If no relevant data, clearly explain what is/isn't available

## Key Messages for Users

When data is not available, be specific:
- ❌ "No data found" (too vague)
- ✅ "Somalia has population and food security data available, but refugee data is not
  available in HDX for this country"

When data is available, explain the coverage:
- ✅ "Afghanistan has refugee data available at country level (admin 0) and province level
  (admin 1) from 2020-2024"

## Remember: Verification First, Query Second

**The metadata_data_availability_get tool is your data compass - use it before every
data expedition.**
"""
