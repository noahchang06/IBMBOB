import React, { useState } from 'react';
import { DomainType, DOMAIN_LABELS } from '../../types';

interface CreateInspirationFormProps {
  onClose: () => void;
  onCreate: (inspiration: any) => void;
  error?: string | null;
}

export function CreateInspirationForm({ onClose, onCreate, error }: CreateInspirationFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [domain, setDomain] = useState<DomainType | ''>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain) {
        alert("Please select a domain.");
        return;
    }
    const inspirationData = {
      name,
      description,
      domain,
    };
    onCreate(inspirationData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-1 p-8 rounded-lg shadow-lg w-full max-w-lg">
        <h2 className="text-2xl font-bold mb-4">Add New Inspiration</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-text-secondary">Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={e => setName(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-surface-2 border border-border rounded-md shadow-sm focus:outline-none focus:ring-accent focus:border-accent"
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-text-secondary">Description</label>
            <textarea
              id="description"
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              className="mt-1 block w-full px-3 py-2 bg-surface-2 border border-border rounded-md shadow-sm focus:outline-none focus:ring-accent focus:border-accent"
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="domain" className="block text-sm font-medium text-text-secondary">Domain</label>
            <select
                id="domain"
                value={domain}
                onChange={e => setDomain(e.target.value as DomainType)}
                className="mt-1 block w-full px-3 py-2 bg-surface-2 border border-border rounded-md shadow-sm focus:outline-none focus:ring-accent focus:border-accent"
                required
            >
                <option value="" disabled>Select a domain</option>
                {Object.keys(DOMAIN_LABELS).map(d => (
                    <option key={d} value={d}>{DOMAIN_LABELS[d as DomainType]}</option>
                ))}
            </select>
          </div>
          {error && (
            <p className="mb-4 text-sm text-red-400">{error}</p>
          )}
          <div className="mt-6 flex justify-end space-x-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-text-secondary bg-surface-2 rounded-md hover:bg-surface-3">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-accent rounded-md hover:bg-accent-bright">
              Add Inspiration
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
