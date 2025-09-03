"""
HDX MCP Server - Population Data Guidance Prompt.

This module contains the population data guidance prompt that helps users
understand how to effectively query population data from HDX.
"""


async def population_data_guidance() -> str:
    """
    Guidance for querying population data from HDX.

    Provides information about available population-related tools and data
    availability considerations.

    Returns:
        Formatted guidance text for population data queries
    """
    return """# HDX Population Data Guidance

## Relevant Tools for Population Queries

When working with population data in HDX, these tools are most useful:

### Primary Population Tools:
- **baseline_population_get**: Subnational population statistics disaggregated by age
  and gender from UNFPA and
    OCHA
- **affected_people_refugees_get**: Annual refugee and persons of concern data from UNHCR
- **affected_people_idps_get**: Internally displaced persons statistics
- **affected_people_returnees_get**: Returnee population data
- **affected_people_humanitarian_needs_get**: People in need of humanitarian assistance

### Supporting Tools:
- **metadata_location_get**: Get location codes and names for population queries
- **metadata_admin1_get** / **metadata_admin2_get**: Administrative boundary information
- **metadata_dataset_get**: Dataset metadata and source information

## Important Data Availability Notes

⚠️ **Data Availability Considerations:**
- Population data may not be available for the current year or previous year for some countries
- When recent data is missing, try querying data from 2-3 years back
- Some countries update population statistics on different schedules
- Crisis-affected areas may have delayed or incomplete data reporting

## Query Tips

1. **Start broad**: Query by country first, then narrow down to specific regions
2. **Check multiple years**: If current year data is missing, try previous years
3. **Use 'all' defaults**: The system defaults age_range and gender to 'all' for comprehensive data
4. **Combine tools**: Use metadata tools to understand data sources and coverage

## ⚠️ CRITICAL: Never Manually Aggregate Population Data

**IMPORTANT: Never sum data yourself, only take the data verbatum
from the tool. If you do not have data at the correct aggregate
level, inform the user.**

**NEVER aggregate totals yourself to answer a question if you do not have the values "
"already aggregated from the tool.**

- **Do NOT** sum population figures from subnational areas to get country totals
- **Do NOT** manually add up age groups or demographic segments
- **Do NOT** combine data from different time periods yourself
- **If pre-aggregated data is not available**, inform the user rather than calculating manually
- **Use the highest admin level** that has the aggregated data you need

## Example Workflow
1. Use `metadata_location_get` to find the correct country code
2. Query `baseline_population_get` for general population statistics
3. Query `affected_people_*` tools for crisis-affected populations
4. If data is missing, try queries with earlier reference periods

This guidance helps ensure you get the most complete and relevant population data from HDX."""
