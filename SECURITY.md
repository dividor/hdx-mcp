# Security Considerations for HDX MCP Server

To report any security issues associated with this repo, please raise an [issue](https://github.com/dividor/hdx-mcp/issues).

This document outlines the security practices implemented in the HDX MCP Server and provides guidance for secure deployment and usage.

## Security Best Practices Implemented

### 1. Authentication & API Key Management

#### ✅ Environment-Based Configuration
- API keys are stored in environment variables, never hardcoded
- API keys are validated at startup but never logged
- Configuration template provided for setup guidance

#### ✅ Secure API Key Transmission
- API keys transmitted via HTTP headers and query parameters as required by HDX
- App identifiers properly base64 encoded per HDX specification
- HTTPS-only communication with HDX API

### 2. Input Validation & Sanitization

#### ✅ Schema-Based Validation
- FastMCP automatically validates inputs against OpenAPI schemas
- Type hints enforce parameter types for custom tools
- Proper error handling prevents information leakage

#### ✅ Custom Tool Validation
```python
async def custom_tool(dataset_hdx_id: str) -> Dict[str, Any]:
    """Proper type hints ensure input validation"""
    if not dataset_hdx_id.strip():
        return {"error": "dataset_hdx_id cannot be empty"}
```

#### ✅ FastMCP Framework Security
- **Automatic Schema Validation**: FastMCP validates all inputs against OpenAPI schemas before execution
- **Type Safety**: Strong typing enforcement prevents type confusion attacks
- **Request Sanitization**: Automatic sanitization of request parameters and headers
- **Response Filtering**: Structured response handling prevents data leakage
- **Error Boundary**: FastMCP provides controlled error handling that prevents stack trace exposure
- **Transport Security**: Built-in support for secure stdio and HTTP transports
- **Resource Management**: Automatic cleanup of resources and connections
- **Protocol Compliance**: Full MCP (Model Context Protocol) specification compliance with security best practices

### 3. Network Security

#### ✅ HTTPS Communication
- All HDX API communication uses HTTPS
- Proper SSL certificate validation
- No fallback to HTTP

#### ✅ Timeout Protection
```python
# Prevents hanging connections
client = httpx.AsyncClient(
    base_url=self.base_url,
    timeout=30.0  # 30 second timeout
)
```

#### ✅ Connection Management
- Proper connection cleanup on shutdown
- Graceful error handling for network failures
- Resource cleanup in finally blocks

### 4. Error Handling

#### ✅ Information Disclosure Prevention
- API keys never appear in error messages or logs
- Detailed errors logged server-side, generic errors returned to clients
- Stack traces sanitized in production

#### ✅ Graceful Degradation
```python
try:
    response = await self.client.get("/endpoint")
    return {"status": "success", "data": response.json()}
except Exception as e:
    logger.error(f"API call failed: {e}")  # Detailed server-side
    return {"error": "API call failed"}    # Generic client-side
```

### 5. Data Handling

#### ✅ No Persistent Storage
- Server maintains no persistent data storage
- All data retrieved fresh from HDX API
- No caching of sensitive information

#### ✅ Memory Management
- Proper cleanup of HTTP responses
- No retention of API responses beyond request scope
- Garbage collection of large objects

### 6. Transport Security

#### ✅ Stdio Transport Security
- Local-only communication
- No network exposure by default
- Suitable for local AI assistant integration

#### ✅ HTTP Transport Security
- Configurable host binding (defaults to localhost)
- Port configuration for controlled access
- No authentication built-in (relies on network security)

## Deployment Security Guidelines

### 1. Environment Configuration

#### Secure Environment Setup
```bash
# Use strong application identifiers
HDX_APP_IDENTIFIER=your_hdx_app_identifier_here

# Never commit secrets to version control
# Use secure environment variable management in production
```

#### Production Considerations
```bash
# Bind to localhost only in production
MCP_HOST=localhost

# Use non-default ports
MCP_PORT=9876

# Consider using environment-specific configs
```

### 2. Network Security

#### Local Deployment (Recommended)
```bash
# Run with stdio transport for maximum security
python hdx_mcp_server.py

# Or HTTP on localhost only
python hdx_mcp_server.py --transport http --host localhost
```

#### Remote Deployment (If Required)
```bash
# Use reverse proxy with authentication
# Configure firewall rules
# Use VPN or private networks
python hdx_mcp_server.py --transport http --host 0.0.0.0
```

### 3. Monitoring & Logging

#### Security Monitoring
```python
# Enable verbose logging for security monitoring
python hdx_mcp_server.py --verbose

# Monitor for:
# - Failed authentication attempts
# - Unusual API usage patterns
# - Network connection failures
# - Unexpected error rates
```

#### Log Security
- Logs never contain API keys or sensitive data
- Consider log rotation and secure storage
- Monitor logs for security events

## Vulnerability Assessment

### 1. Attack Vectors & Mitigations

#### API Key Exposure
- **Risk**: API keys could be exposed in logs, errors, or memory dumps
- **Mitigation**: Environment variables, no logging, secure error handling
- **Status**: ✅ Mitigated

#### Man-in-the-Middle Attacks
- **Risk**: API communication could be intercepted
- **Mitigation**: HTTPS-only communication, certificate validation
- **Status**: ✅ Mitigated

#### Denial of Service
- **Risk**: Malicious clients could overwhelm the server
- **Mitigation**: Request timeouts, connection limits, proper error handling
- **Status**: ✅ Mitigated

#### Code Injection
- **Risk**: Malicious input could execute arbitrary code
- **Mitigation**: Schema validation, type hints, no eval/exec usage
- **Status**: ✅ Mitigated

### 2. Security Boundaries

#### Client Trust Boundary
- MCP clients are assumed to be trusted
- No authentication between MCP client and server
- Network security controls access

#### HDX API Trust Boundary
- HDX API is trusted for data integrity
- Server validates responses but trusts HDX data
- API key provides authentication to HDX

### 3. Data Flow Security

```
[MCP Client] --stdio/HTTP--> [HDX MCP Server] --HTTPS--> [HDX API]
     ^                              ^                        ^
  Local only               Environment vars           API key auth
  No encryption            Timeout protection        HTTPS encryption
```

## Security Testing

### 1. Automated Security Tests

#### API Key Protection
```python
def test_api_key_not_logged(caplog):
    """Ensure API key never appears in logs"""
    server = HDXMCPServer()
    for record in caplog.records:
        assert "test_api_key" not in record.getMessage()
```

#### Input Validation
```python
def test_invalid_inputs():
    """Test handling of malicious inputs"""
    # Empty strings, None values, oversized inputs, etc.
```

### 2. Manual Security Testing

#### Penetration Testing Checklist
- [ ] API key extraction attempts
- [ ] Input fuzzing with malicious payloads
- [ ] Network traffic analysis
- [ ] Memory dump analysis
- [ ] Log file inspection
- [ ] Error message analysis

## Incident Response

### 1. API Key Compromise

If you suspect your HDX API key has been compromised:

1. **Immediate Actions**:
   ```bash
   # Stop the server immediately
   pkill -f hdx_mcp_server.py

   # Rotate your HDX API key
   # Update environment configuration with new key
   # Restart server with new key
   ```

2. **Investigation**:
   - Review server logs for unusual activity
   - Check HDX account for unexpected usage
   - Analyze network traffic if possible

3. **Recovery**:
   - Generate new HDX API key
   - Update environment configuration
   - Monitor for continued suspicious activity

### 2. Server Compromise

If the server itself is compromised:

1. **Containment**:
   - Isolate the server from network
   - Stop all running processes
   - Preserve logs for analysis

2. **Assessment**:
   - Determine scope of compromise
   - Check for data exfiltration
   - Review system integrity

3. **Recovery**:
   - Rebuild server from clean sources
   - Rotate all credentials
   - Implement additional monitoring

## Compliance Considerations

### 1. Data Protection

#### Personal Data Handling
- Server does not store personal data
- All data retrieved from HDX public datasets
- No GDPR implications for server operation

#### Data Residency
- Data processed in memory only
- No cross-border data transfer by server
- HDX API calls may cross borders

### 2. Terms of Service

#### HDX API Usage
- Comply with HDX terms of service
- Respect rate limiting guidelines
- Use data responsibly

#### Organizational Policies
- Follow internal security policies
- Obtain necessary approvals for API usage
- Document security controls

## Security Contact

For security-related issues:

1. **Server Security Issues**: Report via GitHub issues (for non-sensitive issues)
2. **HDX API Security**: Contact HDX support directly
3. **Sensitive Security Issues**: Contact repository maintainers directly

## Security Changelog

### v1.0.0
- Initial security implementation
- Environment-based API key management
- HTTPS-only communication
- Input validation and error handling
- Comprehensive security testing

---

**Note**: This security documentation should be reviewed regularly and updated as the server evolves. Consider periodic security audits and penetration testing for production deployments.
