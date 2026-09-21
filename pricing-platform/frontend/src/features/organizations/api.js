import { apiClient } from "../../api/client";

export function updateOrganization({ name, legalName, email, phone, website, country, timezone, currency }) {
  return apiClient
    .put("/organizations/me", {
      name,
      legal_name: legalName || null,
      email,
      phone: phone || null,
      website: website || null,
      country: country || null,
      timezone,
      currency,
    })
    .then((res) => res.data.data);
}
