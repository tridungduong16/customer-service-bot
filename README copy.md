# XelebAgent

## API Endpoint

The `/ask` endpoint allows users to submit a question related to cryptocurrency and receive an informative response. The API does **not** provide direct financial advice but offers general insights.

```
http://0.0.0.0:8070/ask
```

## Request Format

### Method
`POST`

### Headers
```json
{
  "Content-Type": "application/json"
}
```

### Request Body
The request must contain a JSON object with the `message` field.

#### Example Request
```json
{
  "message": "should I invest into bitcoin"
}
```

## Response Format

### Success Response
- The API returns an informative response based on the user's question.
- The response is in JSON format.

#### Example Response
```json
{
  "response": ""
}
```