export interface Member {
  uid: string;  // Changed to string to handle large Discord UIDs
  display_name: string;
  event_count: number;
  total_amount: number;
  pov_count: number;
  checked_pov_count: number;
  last_pov: string | null;
  last_checked_pov: string | null;
}

export interface Event {
  message_id: string;  // Discord snowflake – string to avoid JS number precision loss
  guild_id: string;
  channel_id: string;
  channel_name: string;
  message_text: string;
  read_time: string | null;
  disband: number;
  points: number | null;
  hidden: number;
}

export interface Payment {
  message_id: string;  // Discord snowflake – string to avoid JS number precision loss
  guild_id: string;
  channel_id: string;
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
  pov_count: number;
  checked_pov_count: number;
  last_pov: string | null;
  last_checked_pov: string | null;
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

// BP / levels & achievements
export interface Level {
  level: number;
  attendance: number;
}

export interface Achievement {
  id: number;
  bp_level: number;
  description: string;
  picture: string;
}

export interface LevelsAndAchievementsResponse {
  levels: Level[];
  achievements: Achievement[];
}

export interface UserAchievementsResponse {
  user: UserDetail;
  achievements: Achievement[];
  total_count: number;
}
