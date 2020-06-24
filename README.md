# Holy Scale

Holy Scale is a cloud experiment to explore the limits of "infintely" scalable serverless apps. The goal of the project is to develop and operate a web service that is guaranteed to always cover its own operating costs - i.e., to have favorable unit economics and (close to) zero fixed costs.

Holy Scale is not just open source, but fully transparent in its operational metrics. Its primary goal is to serve as a conceptual and technology demonstration.

## 100% Utilization. Seriously.

In most web services (those intended to support themselves, anyway), the goal is for the service's revenue to eventually and on average exceed the costs to run, market, and maintain the service. Traditionally, it takes a while for a service to operate "in the black". This delay between start of work and net profit has a few cost components:

1. **Engineering labor costs**. In any sort of pay-as-you-go SaaS offering, development and engineering work precede revenue because customers don't start paying until the service is able to deliver tangible value. This is one reason that the software startup world has come to fetishize iteration and early launches: the sooner a product is validated in the market and begins generating revenue, the sooner a company can slow the rate at which it is burning time and money.

2. **Capital costs**, such as computing and network equipment. The public cloud has largely eliminated this category; for many applications, computing has shifted almost completely to OpEx. For mainstream (non-embedded) computing, the only thing to buy is a laptop.
   
3. **Operational overhead**, 
   1. **Idle (i.e. non-productive) capacity.** This can come in a few flavors, from explicit reservation of capacity (the direct descendant of capital costs) to the idle capacity that must be kept online in order to handle demand volatility.
   2. **Ops labor**. The care and feeding of clusters and other cloud infrastructure, both in steady state and in response to changes in demand.

*Holy Scale is all about rethinking this last cost component.* To be specific, we want to put a target on that part of a service's AWS bill that doesn't generate value, as well as every engineering hour that isn't devoted to high-leverage value creation. Every sliver of expense should carry its own weight, either in directly supporting current delivery or in improving the core value of the system.

But trimming the fat is only half the story, since full utilization is only exciting if the service can meet demand when it comes. So it's crucial to note that, even when we pay the cost to buffer against usage variation, it is still entirely possible to be overtopped by a more extreme demand spike than is planned for. When we say 100% utilization, we mean 100% across a very wide range of usage that fluctuates unpredictably over a wide band.

## Isn't low enough good enough?

Many modern distributed web applications and SaaS services are already architected with these considerations in mind, although not carried to their logical extreme. For example, core system components are run as containerized services inside flexible clusters, with message queues to provide backpressure and smooth out demand spikes. Behaviors that must respond quickly to highly-variable events in the real world often live in function-as-a-service environments like AWS Lambda, which can scale up and down as needed. Auto-scaling provides an additional tool for demand response. Done right, the modern arsenal can deliver an excellent balance of reliability and efficiency.

And underlying all of these engineering decisions is the reality that, for a service being run at typical SaaS gross margins, these infrastructure costs are a relatively small expense line for the organization as a whole. Engineers are more expensive than marginal instances, and that's before we talk about the sales, marketing, and customer success teams. 

With all of these other elements to worry about, why even try to drive unproductive cloud costs to zero?

Consider a thought experiment: assume a software service that required zero up front investment, and which had profitable unit economics at any scale. That is to say, it had positive margin from the first user, and maintained profitability *without further engineering investment* as usage increased over many orders of magnitude. 

A system like this would be viable in many regimes where traditional SaaS economics are disqualifying. The evaluation of sound investments, and the organizational forms and business models of investors, might shift radically. In particular, the most valuable asset put at risk would be the time of the development team pre-launch - i.e., the opportunity costs. But in the absence of significant capital requirements, risk- and profit-sharing collectives might become newly compelling.

Holy Scale is a proof of concept for exactly this kind of 100% utilization, linearly profitable service.

## Let's talk about ops

Software written and used because there's people whose job it is to write and use it.

Not just job security, but also a bias toward larger organizations, maintaining the need for capital to develop and scale new things.

Virtuous cycle: if serverless were taken more seriously, the tooling for interesting use cases would get more attention, then attract more serious people, and on and on. 

## Architectural Constraints

All costs must attached to a paid event. In some cases, this connection will be direct and easy to track; many actions, though, will rely on some bookkeeping to ensure.

1. No long-running processes or server instances
2. No regularly-scheduled jobs
3. No permanent storage

## Technologies


