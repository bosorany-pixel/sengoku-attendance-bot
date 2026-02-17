import type { 
  Member, 
  Event, 
  Payment, 
  Archive, 
  HealthStatus,
  UserEventsResponse,
  UserPaymentsResponse,
  ArchivesListResponse
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  return response.json();
}

/** Raw member from API (uid may be number in JSON; we normalize to string). */
type RawMember = Omit<Member, 'uid'> & { uid: string | number };

/** Ensure UID is always a string (backend may send number; JS loses precision for large ints). */
function normalizeMember(m: RawMember): Member {
  return { ...m, uid: String(m.uid) };
}

export const api = {
  getMembers: async (db?: string): Promise<Member[]> => {
    const query = db ? `?db=${db}` : '';
    const response = await fetchAPI<{ members: RawMember[]; total_count: number }>(`/members${query}`);
    return response.members.map(normalizeMember);
  },

  getUserEvents: async (uid: string, db?: string): Promise<Event[]> => {
    const query = db ? `?db=${db}` : '';
    const response = await fetchAPI<UserEventsResponse>(`/members/${uid}/events${query}`);
    return response.events;
  },

  getUserPayments: async (uid: string, db?: string): Promise<Payment[]> => {
    const query = db ? `?db=${db}` : '';
    const response = await fetchAPI<UserPaymentsResponse>(`/members/${uid}/payments${query}`);
    return response.payments;
  },

  getArchives: async (): Promise<Archive[]> => {
    const response = await fetchAPI<ArchivesListResponse>('/archives');
    return response.archives;
  },

  getHealth: (): Promise<HealthStatus> => {
    return fetchAPI<HealthStatus>('/health');
  },
};
