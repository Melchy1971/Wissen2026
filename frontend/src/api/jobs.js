import { requestJson } from './client.js';

export async function getJob(jobId) {
  return requestJson(`/api/v1/jobs/${jobId}`);
}