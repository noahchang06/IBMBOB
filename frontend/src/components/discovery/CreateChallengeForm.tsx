import React, { useState } from 'react';
import { DomainType, DOMAIN_LABELS } from '../../types';

interface CreateChallengeFormProps {
  onClose: () => void;
  onCreate: (challenge: any) => void;
}

export function CreateChallengeForm({ onClose, onCreate }: CreateChallengeFormProps) {
  const [name, setName] = useState('');
  const [subtitle, setSubtitle] = useState('');
  const [description, setDescription] = useState('');
  const [domains, setDomains] = useState<DomainType[]>([]);
  const [tags, setTags] = useState('');

  const handleDomainChange = (domain: DomainType) => {
    setDomains(prevDomains => 
      prevDomains.includes(domain) 
        ? prevDomains.filter(d => d !== domain)
        : [...prevDomains, domain]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const challengeData = {
      name,
      subtitle,
      description,
      domains,
      tags: tags.split(',').map(tag => tag.trim()),
    };
    onCreate(challengeData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-surface-1 p-8 rounded-lg shadow-lg w-full max-w-lg">
        <h2 className="text-2xl font-bold mb-4">Create New Challenge</h2>
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
            <label htmlFor="subtitle" className="block text-sm font-medium text-text-secondary">Subtitle</label>
            <input
              type="text"
              id="subtitle"
              value={subtitle}
              onChange={e => setSubtitle(e.target.value)}
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
            <label className="block text-sm font-medium text-text-secondary">Domains</label>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {Object.keys(DOMAIN_LABELS).map(domain => (
                <label key={domain} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={domains.includes(domain as DomainType)}
                    onChange={() => handleDomainChange(domain as DomainType)}
                    className="h-4 w-4 rounded border-gray-300 text-accent focus:ring-accent"
                  />
                  <span className="text-sm">{DOMAIN_LABELS[domain as DomainType]}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="mb-4">
            <label htmlFor="tags" className="block text-sm font-medium text-text-secondary">Tags (comma-separated)</label>
            <input
              type="text"
              id="tags"
              value={tags}
              onChange={e => setTags(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-surface-2 border border-border rounded-md shadow-sm focus:outline-none focus:ring-accent focus:border-accent"
            />
          </div>
          <div className="mt-6 flex justify-end space-x-4">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-text-secondary bg-surface-2 rounded-md hover:bg-surface-3">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 text-sm font-medium text-white bg-accent rounded-md hover:bg-accent-bright">
              Create Challenge
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
