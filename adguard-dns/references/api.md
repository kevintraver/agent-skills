# AdGuard DNS API reference

Base URL `https://api.adguard-dns.io`. Header `Authorization: ApiKey $ADGUARD_DNS_API_KEY`.
The full OpenAPI spec is at `https://api.adguard-dns.io/swagger/openapi.json`; fetch it and inspect it with `jq` for request and response schemas.

All account-scoped endpoints accept an optional `X-Account-Id` header (`GET /oapi/v1/accounts` lists the accounts you can use).
Array query params repeat the key: `statuses=REQUEST_BLOCKED&statuses=RESPONSE_BLOCKED`.

## Query log

`GET /oapi/v1/query_log`. Params: `time_from_millis`, `time_to_millis`, `limit` (max 1000), `cursor`, `search` (domain substring), and the arrays `dns_servers`, `devices`, `countries`, `companies`, `statuses`, `categories` (ADS, TRACKERS, SOCIAL_MEDIA, CDN, OTHERS).

- Statuses: `NONE`, `REQUEST_BLOCKED`, `RESPONSE_BLOCKED`, `REQUEST_ALLOWED`, `RESPONSE_ALLOWED`, `MODIFIED`, `UNKNOWN`.
- Item fields: `domain`, `time_iso`, `time_millis`, `device_id`, `dns_server_id`, `dns_request_type`, `dns_response_type`, `category_type`, `company_id`, and `filtering_info` (`filtering_status`, `filtering_type`, `filter_rule`, `filter_id`, `blocked_service_id`, `filtering_category_id`).
- `filtering_type` says what filtered the query: `FILTERS`, `USER_FILTER`, `SAFEBROWSING`, `NEWLY_REGISTERED_DOMAINS`, `TYPOSQUATTING`, `HOMOGLYPH`, `PARENTAL_BLOCKED_SERVICE`, `PARENTAL_FILTERING_CATEGORY`, `PARENTAL_ADULT`, `PARENTAL_SCHEDULE`, `PARENTAL_SAFE_SEARCH`, `PARENTAL_YOUTUBE`.
- Pagination: `pages` is an array of `{current, page_cursor, page_number}`. Pass the `page_cursor` of the entry after `current` as `cursor`.
- `DELETE /oapi/v1/query_log` clears the log. It is destructive, so only run it if the user explicitly asks.

## Listing

Use the paginated v2 list endpoints; the v1 versions are deprecated and scheduled for removal in January 2027. They take `limit` (default 10, max 1000) and `cursor`, and return `{items, navigation}`. While `navigation.next` is present, pass its `page_cursor` as `cursor`.

## DNS servers and settings

- `GET /oapi/v2/dns_servers` (`search`, `dns_servers`): servers with `id`, `name`, `default`, `devices_count`, and `settings`.
- `GET|PUT /oapi/v1/dns_servers/{id}/settings`: a PUT updates only the top-level sections it includes. Sections:
  - `user_rules_settings {enabled, rules[]}`: always send the full rules array; it replaces the existing one.
  - `filter_lists_settings {enabled, filter_list[{filter_id, enabled}]}`
  - `blocking_mode_settings {blocking_mode: NONE|NULL_IP|REFUSED|NXDOMAIN|CUSTOM_IP}`
  - `parental_control_settings`, `safebrowsing_settings`, `access_settings`, and flags such as `protection_enabled`, `ip_log_enabled`, `block_private_relay`, `block_chrome_prefetch`, `block_firefox_canary`, `block_ttl_seconds`.
- `GET /oapi/v2/filter_lists` (built-in and custom), `GET /oapi/v1/web_services` (blockable services), `GET /oapi/v1/parental_control_categories`.

## Devices

`GET /oapi/v2/devices` (`search`, `dns_servers`, `devices`); `GET|PUT /oapi/v1/devices/{id}/settings`.

## Statistics

`GET /oapi/v1/stats/{time|domains|devices|companies|companies/detailed|countries|categories|blocked_parental_categories}`, using the same time and filter params as the query log.

## Rule syntax (user rules)

- `||example.com^`: block the domain and all its subdomains.
- `@@||example.com^`: allow it (an exception rule). Allow rules override filter-list blocks.
- `|example.com^`: match the exact hostname only. `! comment`: a comment line.
