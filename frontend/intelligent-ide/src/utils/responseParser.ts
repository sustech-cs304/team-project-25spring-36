export function parseResponse(response: any): any {
  const data = response.data;
  if (data.status === 'success') {
    return data.data; // or return the whole data, depending on your needs
  } else {
    throw new Error(data.message || 'Unknown error');
  }
}