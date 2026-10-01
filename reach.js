const EARTH_RADIUS_KM = 6371;

// Unit vectors of the airports on the sphere: two airports are within d km of each other (great-circle distance)
// exactly when the dot product of their vectors is at least cos(d / EARTH_RADIUS_KM).
function toUnitVectors(airports) {
    const n = airports.length;
    const x = new Float64Array(n), y = new Float64Array(n), z = new Float64Array(n);
    airports.forEach(([, lat, lon], i) => {
        const phi = lat * Math.PI / 180, lambda = lon * Math.PI / 180;
        x[i] = Math.cos(phi) * Math.cos(lambda);
        y[i] = Math.cos(phi) * Math.sin(lambda);
        z[i] = Math.sin(phi);
    });
    return {n, x, y, z};
}

// Returns the minimum number of flights from the start airport to each airport (0 for the start itself),
// where a single flight can be at most rangeKm long. Only airports with eligible[i] set are used; airports that
// can't be reached at all (and ineligible ones) get -1.
function computeFlights(vectors, start, rangeKm, eligible) {
    const {n, x, y, z} = vectors;
    const minDot = Math.cos(Math.min(rangeKm / EARTH_RADIUS_KM, Math.PI));
    const flights = new Int16Array(n).fill(-1);
    flights[start] = 0;
    let frontier = [start];  // Airports reached with the previous number of flights
    let unvisited = [];
    for (let i = 0; i < n; i++) if (i !== start && eligible[i]) unvisited.push(i);
    for (let count = 1; frontier.length > 0; count++) {
        const reached = [], stillUnvisited = [];
        for (const u of unvisited) {
            let found = false;
            for (const f of frontier) {
                if (x[u] * x[f] + y[u] * y[f] + z[u] * z[f] >= minDot) {
                    found = true;
                    break;
                }
            }
            (found ? reached : stillUnvisited).push(u);
        }
        for (const u of reached) flights[u] = count;
        frontier = reached;
        unvisited = stillUnvisited;
    }
    return flights;
}
