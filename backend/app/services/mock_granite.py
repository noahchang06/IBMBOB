"""
MockGraniteAdapter
==================
Offline fallback that mirrors the contract of WatsonXGraniteAdapter.
"""
from typing import Any
from app.services.granite_adapter import GraniteAdapter
from app.models.inspiration import Inspiration, TransferablePrinciple
from app.models.challenge import PresetChallenge
from app.models.common import DomainType, DerivationLabel
from app.models.graph import GraphEdge, EdgeType

MOCK_INSPIRATIONS = {
    DomainType.architecture: [
        Inspiration(
            id="arch-1", name="Salk Institute", domain=DomainType.architecture,
            description="A research institute known for its symmetrical design and use of concrete.",
            historical_context="Designed by Louis Kahn in 1965.",
            key_principles=[TransferablePrinciple(name="Symmetry", description="Creates a sense of balance and order.", source_domain=DomainType.architecture, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Symmetry can be used to create a sense of calm and order in a design."],
            related_concepts=["Symmetry", "Brutalism"],
            design_implications=["Use of strong symmetrical layouts."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="arch-2", name="The High Line", domain=DomainType.architecture,
            description="An elevated linear park, greenway and rail trail created on a former New York Central Railroad spur on the west side of Manhattan in New York City.",
            historical_context="Opened in 2009.",
            key_principles=[TransferablePrinciple(name="Adaptive Reuse", description="The process of reusing an old site or building for a purpose other than which it was built or designed for.", source_domain=DomainType.architecture, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Existing infrastructure can be repurposed to create new public spaces."],
            related_concepts=["Urban renewal", "Landscape architecture"],
            design_implications=["Consider how existing structures can be integrated into new designs."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="arch-3", name="The Crystal Palace", domain=DomainType.architecture,
            description="A cast-iron and plate-glass structure originally built in Hyde Park, London, to house the Great Exhibition of 1851.",
            historical_context="Designed by Joseph Paxton in 1851.",
            key_principles=[TransferablePrinciple(name="Prefabrication", description="Assembling components of a structure in a factory or other manufacturing site, and transporting complete assemblies or sub-assemblies to the construction site where the structure is to be located.", source_domain=DomainType.architecture, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Prefabrication can significantly speed up construction and reduce costs."],
            related_concepts=["Modular design", "Industrial design"],
            design_implications=["Design systems with modular components that can be easily assembled."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="arch-4", name="Fallingwater", domain=DomainType.architecture,
            description="A house designed by architect Frank Lloyd Wright in 1935 in rural southwestern Pennsylvania. The house was built partly over a waterfall.",
            historical_context="Designed by Frank Lloyd Wright in 1935.",
            key_principles=[TransferablePrinciple(name="Organic Architecture", description="A philosophy of architecture which promotes harmony between human habitation and the natural world.", source_domain=DomainType.architecture, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Designs can be integrated with their natural surroundings to create a sense of harmony."],
            related_concepts=["Sustainable design", "Biophilic design"],
            design_implications=["Consider the natural context of a design and how it can be enhanced."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="arch-5", name="The Pantheon", domain=DomainType.architecture,
            description="A former Roman temple, now a church, in Rome, Italy, on the site of an earlier temple commissioned by Marcus Agrippa during the reign of Augustus.",
            historical_context="Completed by the emperor Hadrian and probably dedicated about 126 AD.",
            key_principles=[TransferablePrinciple(name="Oculus", description="A circular opening in the centre of a dome or in a wall.", source_domain=DomainType.architecture, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["A single, focused light source can create a dramatic and inspiring space."],
            related_concepts=["Domes", "Roman architecture"],
            design_implications=["Use of natural light to create focal points and highlight key features."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="arch-6", name="Sydney Opera House", domain=DomainType.architecture,
            description="A multi-venue performing arts centre at Sydney Harbour in Sydney, New South Wales, Australia.",
            historical_context="Designed by Danish architect Jørn Utzon, but completed by an Australian architectural team headed up by Peter Hall, the building was formally opened on 20 October 1973.",
            key_principles=[TransferablePrinciple(name="Expressionism", description="A modernist movement, initially in poetry and painting, originating in Germany at the beginning of the 20th century. Its typical trait is to present the world solely from a subjective perspective, distorting it radically for emotional effect in order to evoke moods or ideas.", source_domain=DomainType.architecture, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Designs can be expressive and sculptural, not just functional."],
            related_concepts=["Sculpture", "Structural engineering"],
            design_implications=["Exploration of form and structure to create iconic and memorable designs."],
            derivation=DerivationLabel.CURATED,
        ),
    ],
    DomainType.biology: [
        Inspiration(
            id="bio-1", name="Biomimicry", domain=DomainType.biology,
            description="The design and production of materials, structures, and systems that are modeled on biological entities and processes.",
            historical_context="The term was coined by Otto Schmitt in the 1950s.",
            key_principles=[TransferablePrinciple(name="Nature as a model", description="Nature has already solved many of the problems we are grappling with.", source_domain=DomainType.biology, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Look to nature for inspiration and solutions."],
            related_concepts=["Bionics", "Bio-inspired design"],
            design_implications=["Use of natural forms and processes in design."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="bio-2", name="Mycelial Networks", domain=DomainType.biology,
            description="The vegetative part of a fungus, consisting of a network of fine white filaments (hyphae).",
            historical_context="Mycelial networks are some of the largest living organisms on Earth.",
            key_principles=[TransferablePrinciple(name="Decentralized Networks", description="A network in which nodes are interconnected but there is no central point of control.", source_domain=DomainType.biology, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Decentralized networks can be more resilient and efficient than centralized ones."],
            related_concepts=["Neural networks", "Internet"],
            design_implications=["Design of distributed systems and networks."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="bio-3", name="Photosynthesis", domain=DomainType.biology,
            description="The process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy.",
            historical_context="The process was first demonstrated by Jan Ingenhousz in 1779.",
            key_principles=[TransferablePrinciple(name="Energy Conversion", description="The process of changing energy from one form to another.", source_domain=DomainType.biology, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Efficient energy conversion is key to sustainable systems."],
            related_concepts=["Solar energy", "Metabolism"],
            design_implications=["Design systems that can efficiently capture and convert energy."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="bio-4", name="Natural Selection", domain=DomainType.biology,
            description="The differential survival and reproduction of individuals due to differences in phenotype.",
            historical_context="The theory was formulated by Charles Darwin and Alfred Russel Wallace.",
            key_principles=[TransferablePrinciple(name="Adaptation", description="The process by which a species becomes fitted to its environment.", source_domain=DomainType.biology, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Systems that can adapt to changing conditions are more likely to survive and thrive."],
            related_concepts=["Evolution", "Fitness landscape"],
            design_implications=["Design systems that are adaptable and can evolve over time."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="bio-5", name="Fibonacci in Nature", domain=DomainType.biology,
            description="The Fibonacci sequence appears in biological settings, such as branching in trees, the arrangement of leaves on a stem, the fruitlets of a pineapple, the flowering of an artichoke, an uncurling fern and the arrangement of a pine cone's bracts.",
            historical_context="The sequence was known to Indian mathematicians as early as the 6th century.",
            key_principles=[TransferablePrinciple(name="Recursive Patterns", description="Patterns that are generated by repeating a process over and over again.", source_domain=DomainType.biology, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Simple recursive rules can generate complex and beautiful patterns."],
            related_concepts=["Fractals", "Golden ratio"],
            design_implications=["Use of recursive algorithms to generate complex and efficient designs."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="bio-6", name="Swarm Intelligence", domain=DomainType.biology,
            description="The collective behavior of decentralized, self-organized systems, natural or artificial.",
            historical_context="The concept was first introduced by Gerardo Beni and Jing Wang in 1989, in the context of cellular robotic systems.",
            key_principles=[TransferablePrinciple(name="Emergent Behavior", description="Complex behaviors that arise from simple rules and interactions.", source_domain=DomainType.biology, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Simple, local interactions can lead to complex and intelligent global behavior."],
            related_concepts=["Ant colony optimization", "Particle swarm optimization"],
            design_implications=["Design of multi-agent systems that can solve problems through collaboration."],
            derivation=DerivationLabel.CURATED,
        ),
    ],
    DomainType.economics: [
        Inspiration(
            id="eco-1", name="Supply and Demand", domain=DomainType.economics,
            description="A fundamental concept in economics that describes the relationship between the quantity of a commodity that producers wish to sell at various prices and the quantity that consumers wish to buy.",
            historical_context="The concept was popularized by Adam Smith in his 1776 book 'The Wealth of Nations'.",
            key_principles=[TransferablePrinciple(name="Equilibrium", description="The state in which market supply and demand balance each other.", source_domain=DomainType.economics, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Understanding the balance between supply and demand is crucial for any market-based system."],
            related_concepts=["Elasticity", "Market clearing"],
            design_implications=["Design systems that can adapt to changes in supply and demand."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="eco-2", name="Game Theory", domain=DomainType.economics,
            description="The study of mathematical models of strategic interaction among rational decision-makers.",
            historical_context="Developed by John von Neumann and Oskar Morgenstern in the 1940s.",
            key_principles=[TransferablePrinciple(name="Strategic Thinking", description="The ability to consider the actions and reactions of other agents in a system.", source_domain=DomainType.economics, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Design systems that account for the strategic behavior of their users."],
            related_concepts=["Prisoner's dilemma", "Nash equilibrium"],
            design_implications=["Design of multi-agent systems and platforms."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="eco-3", name="Comparative Advantage", domain=DomainType.economics,
            description="The ability of an individual or group to carry out a particular economic activity (such as making a specific product) more efficiently than another activity.",
            historical_context="The theory was first described by David Ricardo in his 1817 book 'On the Principles of Political Economy and Taxation'.",
            key_principles=[TransferablePrinciple(name="Specialization", description="Focusing on a specific area of expertise to increase efficiency.", source_domain=DomainType.economics, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Specialization and trade can lead to overall gains in productivity and efficiency."],
            related_concepts=["Opportunity cost", "Division of labor"],
            design_implications=["Design systems that allow for specialization and efficient collaboration."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="eco-4", name="Creative Destruction", domain=DomainType.economics,
            description="A process of industrial mutation that incessantly revolutionizes the economic structure from within, incessantly destroying the old one, incessantly creating a new one.",
            historical_context="Coined by Joseph Schumpeter in his 1942 book 'Capitalism, Socialism and Democracy'.",
            key_principles=[TransferablePrinciple(name="Innovation Cycles", description="The process of innovation leading to the disruption of existing markets and the creation of new ones.", source_domain=DomainType.economics, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Innovation is a disruptive force that drives economic progress."],
            related_concepts=["Disruptive innovation", "Business cycles"],
            design_implications=["Design systems that are resilient to disruption and can foster innovation."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="eco-5", name="Circular Economy", domain=DomainType.economics,
            description="An economic system aimed at eliminating waste and the continual use of resources.",
            historical_context="The term was first used in the 1980s.",
            key_principles=[TransferablePrinciple(name="Cradle-to-Cradle", description="A design philosophy that considers the entire lifecycle of a product.", source_domain=DomainType.economics, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Waste can be designed out of systems, and resources can be reused and recycled."],
            related_concepts=["Sustainability", "Industrial ecology"],
            design_implications=["Design of closed-loop systems that minimize waste and maximize resource utilization."],
            derivation=DerivationLabel.CURATED,
        ),
        Inspiration(
            id="eco-6", name="Behavioral Economics", domain=DomainType.economics,
            description="A method of economic analysis that applies psychological insights into human behavior to explain economic decision-making.",
            historical_context="Pioneered by Daniel Kahneman and Amos Tversky.",
            key_principles=[TransferablePrinciple(name="Nudging", description="Influencing the behavior of individuals without forbidding any options or significantly changing their economic incentives.", source_domain=DomainType.economics, derivation=DerivationLabel.CURATED)],
            transferable_lessons=["Small changes in the presentation of choices can have a significant impact on decision-making."],
            related_concepts=["Cognitive biases", "Heuristics"],
            design_implications=["Design of user interfaces and choice architectures that guide users towards better decisions."],
            derivation=DerivationLabel.CURATED,
        ),
    ],
}

class MockGraniteAdapter(GraniteAdapter):

    async def generate_inspirations(self, challenge: PresetChallenge) -> list[Inspiration]:
        new_inspirations = []
        for domain in challenge.domains:
            if domain in MOCK_INSPIRATIONS:
                for insp in MOCK_INSPIRATIONS[domain]:
                    new_id = f"{challenge.id}-{insp.id}"
                    new_insp = insp.model_copy(update={'id': new_id})
                    new_inspirations.append(new_insp)
        return new_inspirations

    async def generate_edges(self, challenge_id: str, inspirations: list[Inspiration]) -> list[GraphEdge]:
        edges = []
        if len(inspirations) > 1:
            for i in range(len(inspirations)):
                for j in range(i + 1, len(inspirations)):
                    # Add edges based on shared domains for a slightly more realistic graph
                    if inspirations[i].domain == inspirations[j].domain:
                        edges.append(GraphEdge(
                            id=f"{challenge_id}-edge-{i}-{j}",
                            source_id=inspirations[i].id,
                            target_id=inspirations[j].id,
                            edge_type=EdgeType.functional_similarity,
                            weight=0.5,
                            relationship_description="Shared domain.",
                            transferable_insight="Concepts from the same domain often have functional similarities.",
                            evidence=[],
                            derivation=DerivationLabel.AI,
                        ))
        return edges
    
    async def generate_edges_for_new_inspiration(self, challenge_id: str, new_inspiration: Inspiration, existing_inspirations: list[Inspiration]) -> list[GraphEdge]:
        edges = []
        for i, existing_insp in enumerate(existing_inspirations):
            if new_inspiration.domain == existing_insp.domain:
                edges.append(GraphEdge(
                    id=f"{challenge_id}-edge-new-{i}",
                    source_id=new_inspiration.id,
                    target_id=existing_insp.id,
                    edge_type=EdgeType.functional_similarity,
                    weight=0.5,
                    relationship_description="Shared domain.",
                    transferable_insight="Concepts from the same domain often have functional similarities.",
                    evidence=[],
                    derivation=DerivationLabel.AI,
                ))
        return edges
    
    async def extract_principles(self, inspiration_description: str, target_domain: str) -> list[str]:
        return ["Mock principle 1", "Mock principle 2"]

    async def explain_relationship(self, source: dict[str, Any], target: dict[str, Any], edge: dict[str, Any]) -> str:
        return "This is a mock explanation of a relationship."

    async def suggest_alternatives(self, graph: dict[str, Any], constraints: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"id": "mock-alt-1", "concept": "Mock alternative concept", "derivation": "AI"}]

    async def identify_weak_analogies(self, edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"critique": "This is a mock critique of a weak analogy.", "derivation": "AI"}]

    async def explain_design_tradeoff(self, decision: dict[str, Any], constraints: dict[str, Any]) -> str:
        return "This is a mock explanation of a design tradeoff."

    async def generate_reasoning_summary(self, graph: dict[str, Any], constraints: dict[str, Any], design_system: dict[str, Any]) -> str:
        return "This is a mock reasoning summary."
