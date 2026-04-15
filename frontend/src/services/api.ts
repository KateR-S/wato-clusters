import axios from 'axios';
import type { Tree, Person, Relationship, Cluster, ClusterPerson, ClusterRelationship, Match, Hypothesis } from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const login = async (email: string, password: string) => {
  const res = await api.post<{ access_token: string; token_type: string }>('/auth/login', { email, password });
  return res.data;
};

export const register = async (email: string, password: string) => {
  const res = await api.post<{ access_token: string; token_type: string }>('/auth/register', { email, password });
  return res.data;
};

// Trees
export const getTrees = async (): Promise<Tree[]> => {
  const res = await api.get<Tree[]>('/trees');
  return res.data;
};

export const getTree = async (id: number): Promise<Tree> => {
  const res = await api.get<Tree>(`/trees/${id}`);
  return res.data;
};

export const createTree = async (name: string): Promise<Tree> => {
  const res = await api.post<Tree>('/trees', { name });
  return res.data;
};

export const deleteTree = async (id: number): Promise<void> => {
  await api.delete(`/trees/${id}`);
};

// Tree People
export const getTreePeople = async (treeId: number): Promise<Person[]> => {
  const res = await api.get<Person[]>(`/trees/${treeId}/people`);
  return res.data;
};

export const addPerson = async (treeId: number, data: Omit<Person, 'id' | 'tree_id'>): Promise<Person> => {
  const res = await api.post<Person>(`/trees/${treeId}/people`, data);
  return res.data;
};

export const deletePerson = async (treeId: number, personId: number): Promise<void> => {
  await api.delete(`/trees/${treeId}/people/${personId}`);
};

// Tree Relationships
export const addRelationship = async (treeId: number, data: Omit<Relationship, 'id' | 'tree_id'>): Promise<Relationship> => {
  const res = await api.post<Relationship>(`/trees/${treeId}/relationships`, data);
  return res.data;
};

export const deleteRelationship = async (treeId: number, relId: number): Promise<void> => {
  await api.delete(`/trees/${treeId}/relationships/${relId}`);
};

// GEDCOM
export const uploadGedcom = async (treeId: number, file: File, name: string): Promise<Tree> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);
  const res = await api.post<Tree>(`/trees/${treeId}/gedcom`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

// Matches
export const getMatches = async (treeId: number): Promise<Match[]> => {
  const res = await api.get<Match[]>(`/trees/${treeId}/matches`);
  return res.data;
};

export const addMatch = async (treeId: number, data: Omit<Match, 'id' | 'tree_id'>): Promise<Match> => {
  const res = await api.post<Match>(`/trees/${treeId}/matches`, data);
  return res.data;
};

export const deleteMatch = async (treeId: number, matchId: number): Promise<void> => {
  await api.delete(`/trees/${treeId}/matches/${matchId}`);
};

// Hypotheses
export const getHypotheses = async (treeId: number, clusterId: number): Promise<Hypothesis[]> => {
  const res = await api.post<Hypothesis[]>(`/trees/${treeId}/hypotheses`, { cluster_id: clusterId });
  return res.data;
};

// Clusters
export const getClusters = async (): Promise<Cluster[]> => {
  const res = await api.get<Cluster[]>('/clusters');
  return res.data;
};

export const getCluster = async (id: number): Promise<Cluster> => {
  const res = await api.get<Cluster>(`/clusters/${id}`);
  return res.data;
};

export const createCluster = async (name: string): Promise<Cluster> => {
  const res = await api.post<Cluster>('/clusters', { name });
  return res.data;
};

export const deleteCluster = async (id: number): Promise<void> => {
  await api.delete(`/clusters/${id}`);
};

// Cluster People
export const getClusterPeople = async (clusterId: number): Promise<ClusterPerson[]> => {
  const res = await api.get<ClusterPerson[]>(`/clusters/${clusterId}/people`);
  return res.data;
};

export const addClusterPerson = async (clusterId: number, data: Omit<ClusterPerson, 'id' | 'cluster_id'>): Promise<ClusterPerson> => {
  const res = await api.post<ClusterPerson>(`/clusters/${clusterId}/people`, data);
  return res.data;
};

export const deleteClusterPerson = async (clusterId: number, personId: number): Promise<void> => {
  await api.delete(`/clusters/${clusterId}/people/${personId}`);
};

// Cluster Relationships
export const addClusterRelationship = async (clusterId: number, data: Omit<ClusterRelationship, 'id' | 'cluster_id'>): Promise<ClusterRelationship> => {
  const res = await api.post<ClusterRelationship>(`/clusters/${clusterId}/relationships`, data);
  return res.data;
};

export const deleteClusterRelationship = async (clusterId: number, relId: number): Promise<void> => {
  await api.delete(`/clusters/${clusterId}/relationships/${relId}`);
};

export default api;
