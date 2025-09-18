export default function BasicTestPage() {
  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold">🎉 Success!</h1>
      <p className="text-xl mt-4">The app is working. No more white screen!</p>
      <div className="mt-8 p-4 bg-green-100 rounded">
        <p className="text-green-800">✅ React is rendering</p>
        <p className="text-green-800">✅ Tailwind CSS is working</p>
        <p className="text-green-800">✅ Layout is functioning</p>
      </div>
    </div>
  );
}