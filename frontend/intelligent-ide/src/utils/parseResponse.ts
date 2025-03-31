import { AxiosResponse } from 'axios';

export const parseResponse = <T>(response: AxiosResponse<any>): T => {
  if (response.data && response.data.status === 'success' ) {
    if (response.data.data) {
    return response.data.data as T;
    }else{
      return response.data.status as T;
    }
  } else if (response.data && response.data.status === "error") {
    console.error('Bad Request:', response.data.message);
    throw new Error(response.data.message || 'Unknown error');
  } else {
    console.error('Unexpected response format:', response.data);
    throw new Error('Unexpected response format');
  }
};