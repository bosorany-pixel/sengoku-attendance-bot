export interface Member {
  uid: string;  // Changed to string to handle large Discord UIDs
  display_name: string;
  event_count: number;
  total_amount: number;
}

export interface Event {
  message_id: number;
  guild_id: number;
  channel_id: number;
  channel_name: string;
  message_text: string;
  read_time: string | null;
  disband: number;
  points: number | null;
  hidden: number;
}

export interface Payment {
  message_id: number;
  guild_id: number;
  channel_id: number;
  payment_sum: number;
  payment_ammount: number;
  user_amount: number;
  pay_time: string | null;
}

export interface Archive {
  file: string;
  name: string;
}

export interface UserDetail {
  uid: string;  // Changed to string to handle large Discord UIDs
  display_name: string;
}

export interface HealthStatus {
  status: string;
  technical_timeout: boolean;
}

// API Response wrappers
export interface MembersListResponse {
  members: Member[];
  total_count: number;
}

export interface UserEventsResponse {
  user: UserDetail;
  events: Event[];
  total_count: number;
}

export interface UserPaymentsResponse {
  user: UserDetail;
  payments: Payment[];
  total_count: number;
}

export interface ArchivesListResponse {
  archives: Archive[];
}
