export interface User {
  id: number;
  email: string;
}

export interface Person {
  id: number;
  tree_id: number;
  first_name: string;
  last_name: string;
  birth_year?: number;
  sex: 'M' | 'F' | 'U';
  notes?: string;
}

export interface Relationship {
  id: number;
  tree_id: number;
  person1_id: number;
  person2_id: number;
  rel_type: string;
}

export interface Tree {
  id: number;
  name: string;
  created_at: string;
  people: Person[];
  relationships: Relationship[];
}

export interface ClusterPerson {
  id: number;
  cluster_id: number;
  name: string;
  birth_year?: number;
  notes?: string;
}

export interface ClusterRelationship {
  id: number;
  cluster_id: number;
  person1_id: number;
  person2_id: number;
  rel_type: string;
}

export interface Cluster {
  id: number;
  name: string;
  created_at: string;
  people: ClusterPerson[];
  relationships: ClusterRelationship[];
}

export interface Match {
  id: number;
  tree_id: number;
  person_id: number;
  cluster_person_id: number;
  centimorgans: number;
}

export interface AnchorEntry {
  cluster_person_id: number;
  tree_person_id: number;
  relationship: string;
}

export interface PlacementHypothesis {
  cluster_person_id: number;
  cluster_person_name: string;
  tree_person_id: number;
  tree_person_name: string;
  relationship: string;
  cm_observed: number;
  cm_min: number;
  cm_max: number;
  score: number;
}

export interface Hypothesis {
  rank: number;
  likelihood_score: number;
  likelihood_percent: number;
  placements: PlacementHypothesis[];
}
