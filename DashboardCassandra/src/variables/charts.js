const fetchData = async () => {
  try {
    const response = await fetch('http://localhost:3002/api/data');
    if (!response.ok) {
      throw new Error('Failed to fetch data');
    }
    const data = await response.json();

    // Transformácia dát získaných z backendu na požadovaný formát
    const labels = data.map(entry => new Date(entry.time)); // Predpokladá sa, že time je pole timestampov
    const values = data.map(entry => entry.value); // Predpokladá sa, že value je pole hodnôt

    // Vytvorenie štruktúry dát pre graf
    const chartData = {
      labels: labels,
      datasets: [
        {
          label: 'Data',
          data: values,
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 2,
        },
      ],
    };

    return chartData;
  } catch (error) {
    console.error('Error fetching data:', error);
    return { labels: [], datasets: [] }; // Vrátiť prázdne údaje v prípade chyby
  }
};

export default fetchData;
