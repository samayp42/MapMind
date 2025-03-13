import React from 'react';

const Sidebar = ({ query, setQuery, handleSearch }) => {
  return (
    <div className="sidebar">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter location or query..."
      />
      <button onClick={handleSearch}>Search</button>
    </div>
  );
};

export default Sidebar;