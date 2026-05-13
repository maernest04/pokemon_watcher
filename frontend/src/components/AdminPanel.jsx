import "./AdminPanel.css"

export function AdminPanel({
  user,
  adminUsers,
  expandedAdminUserIds,
  toggleAdminUserExpand,
  handleApprove,
  handleToggleAdmin,
  handleAdminResetPassword,
  handleAdminDelete,
  handleAdminToggleSearch,
  handleAdminDeleteSearch
}) {
  return (
    <section className="dashboard-panel">
      <div className="panel-header">
        <h2>User Management</h2>
        <p className="support-copy">Approve or revoke access for users.</p>
      </div>
      <div className="admin-user-list">
        {adminUsers.map((u) => (
          <div key={u.id} className="admin-user-card" style={{ border: '1px solid var(--border-color)', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <div className="admin-user-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div className="user-info">
                <span className="username">{u.username}</span>
                {u.is_admin && <span className="admin-badge">Admin</span>}
                {!u.is_approved && <span className="pending-badge">Pending</span>}
                <button 
                  type="button" 
                  className="secondary-button" 
                  style={{ marginLeft: '12px', padding: '4px 8px', fontSize: '0.8rem' }} 
                  onClick={() => toggleAdminUserExpand(u.id)}
                >
                  {expandedAdminUserIds.has(u.id) ? 'Hide Searches' : `View Searches (${u.search_queries?.length || 0})`}
                </button>
              </div>
              <div className="user-actions">
                {!u.is_admin && (
                  <button
                    type="button"
                    className={u.is_approved ? "danger-button" : "primary-button"}
                    onClick={() => handleApprove(u.id, !u.is_approved)}
                  >
                    {u.is_approved ? "Revoke Access" : "Approve"}
                  </button>
                )}
                {u.id !== user.id && (
                  <>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => handleToggleAdmin(u.id)}
                    >
                      {u.is_admin ? "Demote" : "Make Admin"}
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => handleAdminResetPassword(u.id)}
                    >
                      Reset Password
                    </button>
                    <button
                      type="button"
                      className="danger-button"
                      onClick={() => handleAdminDelete(u.id)}
                    >
                      Delete
                    </button>

                  </>
                )}
              </div>
            </div>
            {expandedAdminUserIds.has(u.id) && (
              <div className="user-searches-dropdown" style={{ marginTop: '16px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: 'var(--text-color)' }}>User Searches</h4>
                {u.search_queries && u.search_queries.length > 0 ? (
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '8px' }}>
                    {u.search_queries.map(sq => (
                      <li key={sq.id} style={{ padding: '12px', background: 'var(--input-bg)', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <strong>{sq.query_string}</strong>
                          <span style={{ marginLeft: '8px', color: sq.is_active ? '#10b981' : '#ef4444', fontWeight: 500 }}>
                            {sq.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button 
                            type="button" 
                            className="secondary-button" 
                            style={{ padding: '2px 6px', fontSize: '0.75rem' }}
                            onClick={() => handleAdminToggleSearch(u.id, sq.id)}
                          >
                            {sq.is_active ? 'Disable' : 'Enable'}
                          </button>
                          <button 
                            type="button" 
                            className="danger-button" 
                            style={{ padding: '2px 6px', fontSize: '0.75rem' }}
                            onClick={() => handleAdminDeleteSearch(u.id, sq.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="support-copy" style={{ margin: 0, fontSize: '0.85rem' }}>No searches found for this user.</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
