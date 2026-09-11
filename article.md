# Let’s get your first AI Agent out of your laptop

Sometimes, you get tired of hearing about agentic this or that, and want to see for yourself what the fuss is about.

Here, we'll do that together.

I built a simple multi-agent system using Google’s Agent Development Kit, and I’m going to show you how it works, how you can run it locally, deploy it to a production environment, monitor it, and more importantly, how you can do it all on your own using the Agents CLI.

I won’t burden you with tons of code and syntax. Instead, I'll show you how simple it is to do it yourself.

## The multi-agent system we are going to run

I debated for a while whether to share the code of a simple system to save you time, or jump straight into how powerful the Agents CLI is and how you can use it to build whatever you want.

I decided to split the difference and give you both options.

The system I built has two agents that work together. I called them Writer and Editor. Their job is to take an idea you give them and write a short post using it.

I published the source code in the google-cloud-agents repository:

```
git clone https://github.com/svpino/google-cloud-agents.git
cd google-cloud-agents
```

The workflow is simple: the Writer agent processes the input idea, writes a first draft, and then sends it to the Editor agent. The Editor’s job is to criticize the post and provide feedback to the Writer, restarting the process.

I wrote the prompts for each agent to force mistakes and feedback. This keeps the system interesting and lets the workflow loop more than once. Obviously, we don’t want this to run forever, so I limited it to three rounds before stopping.

This is a small, fun system, but it’s enough to show why agent collaboration can be useful: each agent has a specific job, they share information during the process using shared state, and a few simple rules coordinate their interactions.

I published the codebase to save you some time, but honestly, most of the fun will come from using your favorite coding agent to build it from scratch.

## Building your own agentic system from scratch

When you combine the Agents CLI with a coding agent like Codex or Claude Code, magic will happen.

I use Codex, but the CLI will work with any coding agent that supports skills. Run this command to install it:

```
uvx google-agents-cli setup
```

Then restart your coding agent, and you are ready to go.

Let’s start by rebuilding the same system I built without writing a single line of code. This is exactly what I did to build mine. Use this prompt:

```
Use agents-cli to build two agents that work together to craft a post of around 300 characters based on an idea. The Writer agent will draft it. The Editor agent will review it and give feedback in very simple, plain language. The Writer will revise the text and send it back. End when the Editor has no more feedback or after three rounds. Start by creating a local prototype. We will deploy it later.
```

The CLI will help your coding agent do the right thing, but it won’t do anything without you. Codex will ask questions, create a specification, and start working only after you approve it. If you've suffered from coding agents doing too much and taking too many attributions, using Agents CLI will feel like a breath of fresh air.

Depending on how complex your system is, your coding agent will work for some time. It has several things to do, including setting up your local environment, writing the code and configurations, and building an evaluation suite.

When it finishes, you’ll have a working system ready to run. 

And you didn’t have to write a single line of code.

## Running your system locally

Before we send anything to the cloud, we want to run the system locally, play with it for a bit, and make sure it works.

Your coding agent can run it for you, but I prefer to have a separate terminal and run the system myself:

```
agents-cli run
```

This is a quick, easy way to ensure everything works. Type your idea and watch both agents collaborate on the post.

But there’s a more interesting way to run and test the system: the playground. Whoever designed this playground deserves a raise. Run it with this command:

```
agents-cli playground
```

The playground is a browser-based interface. I find it much more useful than running agents from the terminal, especially because the Agents CLI displays a ton of information about the agents, including some good-looking diagrams that show how they interact.

Once you start using the playground, everything else will seem archaic in comparison.

## Good, local results are not enough

The playground makes it easy to fall in love with your system, but that is not enough to test an application. You need a process to evaluate the system. This is even more critical if you are planning to keep improving it over time.

Of course, the good folks behind the Agents CLI thought about this. When you typed the initial prompt to build everything, your coding agent generated a simple evaluation harness to test the system. This harness includes unit and integration tests, and a simple evaluation dataset with examples to stress-test the agents.

You’ll find the dataset I created in `tests/eval/datasets/basic-dataset.json`. It includes four examples to help ensure the agents generate posts without any jargon while preserving the original meaning of the input idea.

Every time you ask your coding agent to change the system, the Agents CLI will force it to run the evaluations, but you can also run them manually:

```
agents-cli eval run
```

The code I published checks post length and ensures the workflow doesn’t run more than three times. Using the model as a judge, another evaluator will check whether the post preserves the input idea and uses clear and simple language.

I’m sure you can come up with several other useful tests, and you can ask your coding agent to create them for you:

```
Write an evaluation that ensures the final post contains no em dashes or emojis.
```

A lesson I learned the hard way: A system without automatic evaluations is nothing more than a prompt that worked once. 

## Deploying the system to Cloud Run

After you get tired of running the system locally, it’s time to deploy it and make it available to everyone.

We'll use Cloud Run for this.

I bet you an ice cream you’ve never seen a faster, simpler way to deploy code before, especially when you know this will require some tricky infrastructure configs.

Cloud Run needs a container to run our app, but we’ll let the Agents CLI worry about that. Once we deploy the system, we’ll get an HTTPS service we can share with whoever wants to try the fruit of our labor. 

To use Cloud Run, you need to authenticate with Google Cloud and select the project where you want to deploy the system. You can do that in your browser or by running the following commands:

```
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

After you figure that out, you can go back to your coding agent and let the magic happen with a simple prompt:

```
Deploy to Cloud Run
```

With Cloud Run, you don’t have to worry about infrastructure, configurations, or dealing with a Kubernetes cluster. You don’t have to worry about how the deployment will happen or the specific commands you’d have to run.

Your coding agent will do it for you.

Agents CLI will help your coding agent create the configuration, build the container, upload it, and create the Cloud Run service. When it finishes, it will print back the service URL. You can also view the service in the Google Cloud Console.

That URL is everything you need to run the service. Here is the command you want to run after replacing `YOUR_CLOUD_RUN_URL` with the proper value:

```
agents-cli run \
  --url YOUR_CLOUD_RUN_URL \
  --mode adk \
  "Julius Caesar was a great consul"
```

The command will call the ADK streaming interface exposed by the Cloud Run service. Your application will immediately start streaming its responses back to the terminal.

Everything will work exactly as it did before when you ran it locally.

## Looking behind the curtain

In my code, I’m logging a few different events as the agents do their work. This is crucial if I later want to see how the deployed system is working.

I’m only logging the minimum necessary. I’d recommend you add more logs.

Cloud Run will collect these logs automatically and send them to Cloud Logging. You can inspect these logs from the Cloud Run service page or query them from the terminal. 

This is the prompt I usually use when I’m too lazy to look up the proper command:
    
```
Display any logs from Cloud Run for the "agent_idea" and "agent_final_response" events.
```

Did I mention how much I like the Agents CLI? Well, I do.

By the way, logs can only tell you something that happens in your system at a specific moment in time. They are useful, but they aren’t enough.

You also want traces, which are more comprehensive than logs. A trace will help you understand the path your system took between point A and point B. I think about traces as the complete “story” of a request.

Cloud Run will send traces to Cloud Trace. You can find them in the Google Cloud Console, or, again, you can ask your coding agent for them:

```
Show any traces from Cloud Run
```

Keep in mind, there are never too many logs.

Logging as much as possible is one of those habits I built since when print statements were everything we had. 

Remember this.

## Where to go from here

I know this entire article is for fun and learning purposes, but we could still roleplay and pretend this is just the beginning of a much more complex system.

If I wanted to move from here, I would start by expanding the evaluation set. 

We need many more examples. I would test the agents to understand how they process vague ideas, very long inputs, unusual punctuation, and anything else that could break them.

I’d also consider load testing, especially if I know many people will be using this simultaneously.

Load testing sounds fancier than it is: start sending multiple requests at once and measure how long the agents take to respond, how much memory they use, and whether they fail. This will show you your system's limits.

You can also consider configuring Cloud Run’s traffic splitting when releasing large changes. This keeps most users on the working version while testing the new changes with a small percentage of requests.

There’s so much more I’d do, but I want to finish the article with a summary of the most important ideas I tried to touch on:

1. Start with something simple. You don’t need a sophisticated idea to learn agents.
2. The Agents CLI will make your coding agent dramatically more useful. 
3. Build an end-to-end prototype first. Worry about deploying it later.
4. Automatic evaluations are essential. 
5. Production means deployment plus observability.

Have fun!

