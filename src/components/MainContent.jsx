import { useState } from 'react';

const stats = [
  { label: 'Total Users', value: '12,480' },
  { label: 'Revenue', value: '$84,320' },
  { label: 'Active Projects', value: '34' },
  { label: 'Completion Rate', value: '91%' },
];

const initialTasks = [
  { id: 1, text: 'Review pull requests' },
  { id: 2, text: 'Update documentation' },
  { id: 3, text: 'Deploy to staging' },
];

export default function MainContent() {
  const [tasks, setTasks] = useState(initialTasks);
  const [input, setInput] = useState('');

  function addTask() {
    const text = input.trim();
    if (!text) return;
    setTasks((prev) => [...prev, { id: Date.now(), text }]);
    setInput('');
  }

  function removeTask(id) {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') addTask();
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-semibold text-gray-800 mb-8">Welcome back</h1>

      {/* Stat cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        {stats.map(({ label, value }) => (
          <div
            key={label}
            className="bg-white rounded-xl border border-gray-200 shadow-sm p-6"
          >
            <p className="text-sm text-gray-500 mb-1">{label}</p>
            <p className="text-2xl font-bold text-gray-800">{value}</p>
          </div>
        ))}
      </section>

      {/* Task list */}
      <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 max-w-lg">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Tasks</h2>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="New task..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={addTask}
            className="rounded-lg bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 text-sm font-medium transition-colors"
          >
            Add
          </button>
        </div>

        <ul className="space-y-2">
          {tasks.map(({ id, text }) => (
            <li
              key={id}
              className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-sm text-gray-700"
            >
              <span>{text}</span>
              <button
                onClick={() => removeTask(id)}
                className="ml-4 text-gray-400 hover:text-red-500 transition-colors text-xs font-medium"
              >
                Remove
              </button>
            </li>
          ))}
          {tasks.length === 0 && (
            <li className="text-sm text-gray-400 text-center py-4">No tasks yet.</li>
          )}
        </ul>
      </section>
    </main>
  );
}
