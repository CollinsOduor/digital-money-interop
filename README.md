This project explores the case for interoperability between mobile money service providers in Kenya. It introduces a Fintech layer between the 2 service providers to ensure quick movement of cash for agents. In short, we are envisioning a scenario where an agent can service both Safaricom and Airtel clients while utilizing the same float they have. The client would just need to move float from Airtel to Safaricom, or vice versa.

## Getting Started

### Prerequisites for running this POC:

1. Docker installed. Alternatively, you can install the required packlages globally to bypass this requirement.
2. Node > v22

First, run the development server:

1. Backend:

```bash
docker build -t digital-money-interop:latest .
# then
docker run -p 8000:8000 digital-money-interop:latest
```

1. Frontend:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
