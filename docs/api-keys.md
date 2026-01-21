# API KEY REFERENCES

## Environment Variables
```
# .env
GOOGLEAI_API_KEY='YourAPIkey'
OPENAI_API_KEY='YourAPIkey'
OPENROUTER_API_KEY='YourAPIkey'
OLLAMA_API_KEY='ollama'
```

## How to Get API Keys

### Google AI
1. Visit https://aistudio.google.com/app/apikey.
2. Accept the Terms and Conditions.
3. Click "Create API key".
4. Name your key.
5. Choose project > Create project.
6. Select the newly created project.
7. Click "Create key".
8. Click the code in the "Key" column.
9. Click "Copy key".
> [!TIP]
> Gemini API Free Tier has rate limits, see: https://ai.google.dev/gemini-api/docs/rate-limits.
>
> **To check your quota:**
> 1. Visit https://aistudio.google.com/app/usage
> 2. Make sure you are on the right account & project.
> 2. Click "Open in Cloud Console" on the bottom.
> 3. Scroll down > Click "Quotas & System Limits".
> 4. Scroll down > You will see your model quota usage on the top result. If you don't see it, use Filter to search it.
>
> For example: 
    <details>
        <summary>View image</summary>
            <p align="center">
                <img alt="Gemini Free Tier Quota"
    title="Gemini Free Tier Quota" src="../assets/images/gemini-quota.png" />
            </p>
    </details>