# Model Configuration Update

## Overview
Updated the AWS Billing Backend Lambda to support the latest AI models with comprehensive debug logging and model selection capabilities.

## New Default Model
- **Default Model**: `us.anthropic.claude-sonnet-4-20250514-v1:0` (Claude Sonnet 4)
- **Previous Default**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (Claude 3.5 Sonnet v2)

## Supported Models

### Anthropic Claude Models
1. **Claude Sonnet 4** (Default)
   - Model ID: `us.anthropic.claude-sonnet-4-20250514-v1:0`
   - Max Tokens: 4000
   - Temperature: 0.7

2. **Claude 3.7 Sonnet**
   - Model ID: `us.anthropic.claude-3-7-sonnet-20250109-v1:0`
   - Max Tokens: 4000
   - Temperature: 0.7

3. **Claude 3 Haiku**
   - Model ID: `anthropic.claude-3-haiku-20240307-v1:0`
   - Max Tokens: 3000
   - Temperature: 0.7

### Meta Llama Models
4. **Llama 4 Scout 17B Instruct**
   - Model ID: `us.meta.llama4-scout-17b-instruct-v1:0`
   - Max Tokens: 2048
   - Temperature: 0.7

5. **Llama 4 Maverick 17B Instruct**
   - Model ID: `us.meta.llama4-maverick-17b-instruct-v1:0`
   - Max Tokens: 2048
   - Temperature: 0.7

## Key Features

### 1. Model Selection
- **Default Behavior**: Uses Claude Sonnet 4 if no model specified
- **Environment Override**: Can set `AUDIT_MODEL` environment variable
- **Request-Level Selection**: Can specify model in API requests
- **Fallback Protection**: Invalid models automatically fallback to default
- **Smart Error Handling**: Automatic fallback to Claude 3 Haiku for unsupported models
- **Model Availability Check**: Validates model access before invocation

### 2. Debug Logging
All audit requests now include comprehensive debug logging with emojis for easy identification:

```
🔍 AUDIT DEBUG: Processing audit request
📋 AUDIT DEBUG: Requested model: None (using default)
🤖 AUDIT DEBUG: Selected model: us.anthropic.claude-sonnet-4-20250514-v1:0 (Claude Sonnet 4)
🏭 AUDIT DEBUG: Model provider: anthropic
⚙️ AUDIT DEBUG: Model type: claude
📤 AUDIT DEBUG: Sending request to AWS Bedrock
📏 AUDIT DEBUG: Prompt length: 1234 characters
🎛️ AUDIT DEBUG: Max tokens: 4000
🌡️ AUDIT DEBUG: Temperature: 0.7
📥 AUDIT DEBUG: Received response from Claude Sonnet 4
📏 AUDIT DEBUG: Response length: 2345 characters
✅ AUDIT DEBUG: Audit completed successfully using Claude Sonnet 4
�� AUDIT DEBUG: Fraud score: 25.5
```

### 3. Model-Specific Request Formatting
- **Claude Models**: Uses Anthropic's message format with `anthropic_version`
- **Llama Models**: Uses prompt-based format with `max_gen_len`
- **Mistral Models**: Uses prompt-based format with `max_tokens`, `top_p`, `top_k`

### 4. Enhanced Mock System
When Bedrock access is unavailable, the mock system now:
- Shows which model would have been used
- Includes model information in debug logs
- Provides instructions for enabling specific models

## API Changes

### New Endpoints

#### List Available Models
```
GET /api/audit/models
GET /api/audit/models/
```

Response:
```json
{
  "models": [
    {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "name": "Claude Sonnet 4",
      "provider": "anthropic",
      "type": "claude",
      "max_tokens": 4000,
      "temperature": 0.7,
      "is_default": true
    }
  ],
  "default_model": "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "total_models": 5
}
```

### Updated Endpoints

#### Audit Claim with Model Selection
```
POST /api/audit/claims/{claim_id}?model_id=us.anthropic.claude-sonnet-4-20250514-v1:0
```

#### Process Audit with Model Selection
```json
POST /api/audit/process
{
  "claim_data": "...",
  "model_id": "us.meta.llama4-scout-17b-instruct-v1:0"
}
```

#### Ollama Routes with Model Selection
```json
POST /api/ollama/audit
{
  "claim_data": "...",
  "model": "mistral.mistral-7b-instruct-v0:2"
}
```

## Response Enhancements

All audit responses now include detailed model information:

```json
{
  "audit_result": "...",
  "success": true,
  "details": {
    "fraud_score": 25.5,
    "model_used": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "model_name": "Claude Sonnet 4",
    "model_provider": "anthropic",
    "prompt_length": 1234,
    "response_length": 2345,
    "timestamp": "2025-05-26T15:18:04.969Z"
  }
}
```

## Files Modified

### Core Files
- `routes/audit_routes.py` - Main audit system with model configuration
- `routes/ollama_routes.py` - Updated to use new model system
- `lambda_function.py` - No changes needed (uses routes)

### Configuration Files
- `.github/workflows/deploy-lambda.yml` - Updated environment variables
- `github-actions-lambda-policy.json` - No changes needed

### New Files
- `test_models.py` - Test script for model configuration
- `MODEL_CONFIGURATION_UPDATE.md` - This documentation

## Environment Variables

### GitHub Actions / Lambda
```bash
AUDIT_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
CLAUDE_HAIKU_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_REGION=us-east-1
```

## Testing

Run the test script to verify configuration:
```bash
python test_models.py
```

Expected output shows:
- ✅ 5 supported models configured
- ✅ Model selection and fallback working
- ✅ Request body creation for all model types
- ✅ Response parsing for all model types
- ✅ Debug logging system functional

## Deployment

The updated code is ready for deployment via GitHub Actions. The workflow will:
1. Build Docker image with new model configuration
2. Update Lambda function with new environment variables
3. Deploy with enhanced audit capabilities

## Usage Examples

### Use Default Model (Claude Sonnet 4)
```bash
curl -X POST "https://your-lambda-url/api/audit/process" \
  -H "Content-Type: application/json" \
  -d '{"claim_data": "..."}'
```

### Use Specific Model
```bash
curl -X POST "https://your-lambda-url/api/audit/process" \
  -H "Content-Type: application/json" \
  -d '{"claim_data": "...", "model_id": "us.meta.llama4-scout-17b-instruct-v1:0"}'
```

### Audit Claim with Model Selection
```bash
curl -X POST "https://your-lambda-url/api/audit/claims/123?model_id=us.anthropic.claude-3-7-sonnet-20250109-v1:0"
```

### List Available Models
```bash
curl "https://your-lambda-url/api/audit/models"
```

## Benefits

1. **Flexibility**: Support for multiple AI providers and models
2. **Performance**: Can choose optimal model for specific use cases
3. **Cost Optimization**: Can use smaller/cheaper models when appropriate
4. **Debugging**: Comprehensive logging for troubleshooting
5. **Reliability**: Automatic fallback for invalid model selections
6. **Future-Proof**: Easy to add new models as they become available

## Next Steps

1. Deploy the updated code via GitHub Actions
2. Test with different models in production
3. Monitor performance and costs across different models
4. Consider adding model-specific optimizations based on usage patterns 