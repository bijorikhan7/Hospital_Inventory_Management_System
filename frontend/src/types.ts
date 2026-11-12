export type Role = "ADMIN" | "IT_STAFF" | "EMPLOYEE";

export type User = {
  id: number;
  username: string;
  email: string;
  role: Role;
  is_active: boolean;
  employee: number | null;
  employee_name?: string;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Asset = {
  id: number;
  asset_code: string;
  name: string;
  brand: string;
  model: string;
  serial_number: string;
  description?: string;
  status: string;
  condition: string;
  location: string;
  category: number;
  category_name?: string;
  category_code?: string;
  current_employee: number | null;
  employee_name?: string | null;
  vendor?: number | null;
  vendor_name?: string | null;
  purchase_date?: string | null;
  purchase_price?: string | number | null;
  warranty_status?: string | null;
  warranty_until?: string | null;
  qr_payload?: string;
  warranties?: Warranty[];
};

export type Warranty = {
  id: number;
  asset: number;
  provider: string;
  warranty_type: string;
  start_date: string;
  end_date: string;
  warranty_number: string;
  terms: string;
  status: string;
};

export type Employee = {
  id: number;
  employee_code: string;
  name: string;
  email: string;
  phone: string;
  department: string;
  designation: string;
  join_date: string | null;
  location: string;
  status: string;
};

export type DashboardData = {
  assets: Record<string, number>;
  warranties: { active: number; expiring_soon: number; expired: number };
  open_issues: number;
  assets_under_repair: number;
  recent_activities: {
    id: number;
    asset_code: string;
    action: string;
    description: string;
    performed_by: string | null;
    created_at: string;
  }[];
};
