# Chani.AI Agent

## API Endpoint

The `/ask` endpoint allows users to submit a customer service inquiry and receive an informative response. The API provides insights but does **not** replace human customer service agents.

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
  "message": ""
}
```

## Response Format

### Success Response
- The API returns an informative response based on the user's inquiry.
- The response is in JSON format.

#### Example Response
```json
{
  "response": ""
}
```