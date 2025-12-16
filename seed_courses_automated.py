import sys
import os
from sqlalchemy.orm import Session
import random

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import db
import models

def seed_courses():
    session = db.SessionLocal()
    try:
        print("Starting automated course seeding with syllabus...")

        # 1. Fetch Branches to link
        # We assume B.Tech branches exist from previous seeding
        btech_cse = session.query(models.Branch).filter(models.Branch.code == "CSE").first()
        btech_ece = session.query(models.Branch).filter(models.Branch.code == "ECE").first()
        btech_me = session.query(models.Branch).filter(models.Branch.code == "ME").first()
        
        # M.Tech example
        mtech_ai = session.query(models.Branch).filter(models.Branch.name.like("%Computer Science(AI)%")).first()

        if not btech_cse:
            print("CRITICAL: CSE Branch not found. Please run seed_academic_data.py first.")
            return

        # 2. Define Course Data (Code, Title, Semester, Credits, Short Desc, Syllabus)
        
        # --- CSE Courses ---
        cse_courses = [
            {
                "code": "CS101", "title": "Programming for Problem Solving", "semester": 1, "credits": 4,
                "desc": "Introduction to C programming and algorithmic thinking.",
                "syllabus": """UNIT - I: Introduction to Programming
Introduction to components of a computer system: disks, primary and secondary memory, processor, operating system, compilers, creating, compiling and executing a program etc., Number systems.
Introduction to Algorithms: steps to solve logical and numerical problems. Representation of Algorithm, Flowchart/Pseudo code with examples, Program design and structured programming.
Introduction to C Programming Language: variables (with data types and space requirements), Syntax and Logical Errors in compilation, object and executable code , Operators, expressions and precedence, Expression evaluation, Storage classes (auto, extern, static and register), type conversion, The main method and command line arguments Bitwise operations: Bitwise AND, OR, XOR and NOT operators

UNIT - II: Conditional Branching and Loops
Conditional Branching: Writing and evaluation of conditionals and consequent branching with if, if-else, switch-case, ternary operator, goto, Break, Continue.
Loops: Iteration and loops, I-O functions (formatted and unformatted), Control structures- while, do-while, for, nested loops.

UNIT - III: Arrays and Strings
Arrays: one and two dimensional arrays, creating, accessing and manipulating elements of arrays.
Strings: Introduction to strings, handling strings as array of characters, basic string functions available in C (strlen, strcat, strcpy, strstr etc.), arrays of strings.

UNIT - IV: Structures and Pointers
Structures: Defining structures, initializing structures, union, Array of structures.
Pointers: Idea of pointers, Defining pointers, Pointers to Arrays and Structures, Use of Pointers in self-referential structures, usage of self referential structures in linked list (no implementation) Enumeration data type.

UNIT - V: Preprocessor and File handling in C
Preprocessor: Commonly used Preprocessor commands like include, define, undef, if, ifdef, ifndef.
Files: Text and Binary files, Creating and Reading and writing text and binary files, Appending data to existing files, Writing and reading structures using binary files, Random access using fseek, ftell and rewind functions."""
            },
            {
                "code": "CS203", "title": "Data Structures", "semester": 3, "credits": 4,
                "desc": "Fundamental data structures: arrays, stacks, queues, linked lists, trees, and graphs.",
                "syllabus": """UNIT - I: Introduction to Data Structures
Abstract Data Types (ADTs) – List ADT – array-based implementation – linked list implementation – singly linked lists- circularly linked lists- doubly-linked lists – applications of lists –Polynomial Manipulation – All operations (Insertion, Deletion, Merge, Traversal).

UNIT - II: Linear Data Structures
Stack ADT – Operations - Applications - Evaluating arithmetic expressions- Conversion of Infix to postfix expression - Queue ADT – Operations – Circular Queue – Priority Queue – deQueue – applications of queues.

UNIT - III: Non Linear Data Structures
Trees – Binary Trees – Binary tree representation and traversals – Inorder, Preorder, Postorder - Threaded binary trees – binary search trees – definition, ADT, implementation, operations – Search, Insertion and Deletion.

UNIT - IV: Graphs
Graphs – Introduction - Definition – Representation of Graph - Types of graph - Breadth-first traversal - Depth-first traversal - Topological Sort - Bi-connectivity - Cut vertex - Euler circuits - Applications of graphs.

UNIT - V: Searching and Sorting
Searching: Linear Search - Binary Search. 
Sorting: Insertion Sort - Selection Sort - Shell Sort - Bubble Sort - Quick Sort - Heap Sort - Merge Sort - Radix Sort.
Hashing: Functions - separate chaining - open addressing - rehashing - extendible hashing."""
            },
            {
                "code": "CS205", "title": "Database Management Systems", "semester": 3, "credits": 4,
                "desc": "Relational databases, SQL, normalization, and transaction management.",
                "syllabus": """UNIT - I: Introduction
Database System Applications: A Historical Perspective, File Systems versus a DBMS, the Data Model, Levels of Abstraction in a DBMS, Data Independence, Structure of a DBMS.
Introduction to Database Design: Database Design and ER Diagrams, Entities, Attributes, and Entity Sets, Relationships and Relationship Sets, Additional Features of the ER Model, Conceptual Design With the ER Model.

UNIT - II: Relational Model
Introduction to the Relational Model: Integrity constraint over relations, enforcing integrity constraints, querying relational data, logical data base design, introduction to views, destroying/altering tables and views. Relational Algebra, Tuple relational Calculus, Domain relational calculus.

UNIT - III: SQL and Normalization
SQL: Queries, Constraints, Triggers: form of basic SQL query, UNION, INTERSECT, and EXCEPT, Nested Queries, aggregation operators, NULL values, complex integrity constraints in SQL, triggers and active data bases.
Schema Refinement: Problems caused by redundancy, decompositions, problems related to decomposition, reasoning about functional dependencies, FIRST, SECOND, THIRD normal forms, BCNF, lossless join decomposition, multi-valued dependencies, FOURTH normal form, FIFTH normal form.

UNIT - IV: Transaction Management
Transaction Concept, Transaction State, Implementation of Atomicity and Durability, Concurrent Executions, Serializability, Recoverability, Implementation of Isolation, Testing for serializability, Lock Based Protocols, Timestamp Based Protocols, Validation- Based Protocols, Multiple Granularity.

UNIT - V: Storage and Indexing
Data on External Storage: File Organization and Indexing, Cluster Indexes, Primary and Secondary Indexes, Index data Structures, Hash Based Indexing, Tree base Indexing, Comparison of File Organizations, Indexes and Performance Tuning.
Tree Structured Indexing: Intuitions for tree Indexes, Indexed Sequential Access Methods (ISAM), B+ Trees: A Dynamic Index Structure."""
            },
             {
                "code": "CS301", "title": "Artificial Intelligence", "semester": 5, "credits": 3,
                "desc": "Search algorithms, knowledge representation, and basic machine learning concepts.",
                "syllabus": """UNIT - I: Introduction to AI
Introduction: AI problems, Agents and Environments, Structure of Agents, Problem Solving Agents 
Basic Search Strategies: Problem Spaces, Uninformed Search (Breadth-First, Depth-First Search, Depth-first with Iterative Deepening), Heuristic Search (Hill Climbing, Generic Best-First, A*), Constraint Satisfaction (Backtracking, Local Search).

UNIT - II: Advanced Search
Advanced Search: Constructing Search Trees, Stochastic Search, A* Search Implementation, Minimax Search, Alpha-Beta Pruning.
Basic Knowledge Representation and Reasoning: Propositional Logic, First-Order Logic, Forward Chaining and Backward Chaining, Introduction to Probabilistic Reasoning, Bayes Theorem.

UNIT - III: Machine Learning Intro
Introduction to Machine Learning: Supervised, Unsupervised & Reinforcement Learning.
Linear Regression, Logistic Regression.
Decision Trees: ID3, C4.5 algorithms.

UNIT - IV: Neural Networks
Neural Networks: Perceptron, Multi-Layer Perceptron (MLP), Backpropagation algorithm.
Introduction to Deep Learning: Convolutional Neural Networks (CNN) basic architecture.

UNIT - V: NLP & Expert Systems
Natural Language Processing: Introduction, Syntactic Processing, Semantic Analysis.
Expert Systems: Architecture, Knowledge acquisition, Rule-based systems, Applications of Expert Systems."""
            }
        ]

        # --- ECE Courses ---
        ece_courses = [
             {
                "code": "EC201", "title": "Electronic Devices and Circuits", "semester": 3, "credits": 4,
                "desc": "Semiconductor physics, PN junctions, BJT, FET, and their applications.",
                "syllabus": """UNIT - I: P-N Junction Diode
Qualitative Theory of P-N Junction, P-N Junction as a Diode, Diode Equation, Volt-Ampere Characteristics, Temperature dependence of VI characteristic, Ideal versus Practical - Resistance levels (Static and Dynamic), Transition and Diffusion Capacitances, Diode Equivalent Circuits, Load Line Analysis, Breakdown Mechanisms in Semiconductor Diodes, Zener Diode Characteristics.

UNIT - II: Rectifiers and Filters
The P-N junction as a Rectifier, Half wave Rectifier, Full wave Rectifier, Bridge Rectifier, Harmonic components in a Rectifier Circuit, Inductor Filters, Capacitor Filters, L- Section Filters, π- Section Filters, Comparision of Filters, Voltage Regulation using Zener Diode.

UNIT - III: Bipolar Junction Transistor
The Junction Transistor, Transistor Current Components, Transistor as an Amplifier, Transistor Construction, BJT Operation, BJT Symbol, Common Base, Common Emitter and Common Collector Configurations, Limits of Operation, BJT Specifications.

UNIT - IV: Transistor Biasing and Stabilization
Operating Point, The DC and AC Load lines, Need for Biasing, Fixed Bias, Collector Feedback Bias, Emitter Feedback Bias, Collector - Emitter Feedback Bias, Voltage Divider Bias, Bias Stability, Stabilization Factors, Stabilization against variations in VBE and β, Bias Compensation using Diodes and Transistors, Thermal Runaway, Thermal Stability.

UNIT - V: Field Effect Transistor
The Junction Field Effect Transistor (Construction, principle of operation, symbol) - Pinch-off Voltage - Volt-Ampere characteristics, The JFET Small Signal Model, MOSFET (Construction, principle of operation, symbol), MOSFET Characteristics in Enhancement and Depletion modes."""
            },
        ]

        # --- ME Courses ---
        me_courses = [
            {
                "code": "ME202", "title": "Thermodynamics", "semester": 3, "credits": 4,
                "desc": "Laws of thermodynamics, entropy, and thermodynamic cycles.",
                "syllabus": """UNIT - I: Introduction
Basic Concepts: System, Control Volume, Surrounding, Boundaries, Universe, Types of Systems, Macroscopic and Microscopic viewpoints, Concept of Continuum, Thermodynamic Equilibrium, State, Property, Process, Cycle - Reversibility - Quasi - static Process, Irreversible Process, Causes of Irreversibility - Energy in State and in Transition, Types, Work and Heat, Point and Path function.

UNIT - II: Zeroth and First Law
Zeroth Law of Thermodynamics - Concept of quality of Temperature - Principles of Thermometry - Reference Points - Const. Volume gas Thermometer - Scales of Temperature, Ideal Gas Scale - PMM I - Joule's Experiments - First law of Thermodynamics - Corollaries - First law applied to a Process - applied to a flow system - Steady Flow Energy Equation.

UNIT - III: Second Law
Limitations of the First Law - Thermal Reservoir, Heat Engine, Heat pump, Parameters of performance, Second Law of Thermodynamics, Kelvin-Planck and Clausius Statements and their Equivalence / Corollaries, PMM of Second kind, Carnot's principle, Carnot cycle and its specialties, Thermodynamic scale of Temperature, Clausius Inequality, Entropy, Principle of Entropy Increase - Energy Equation, Availability and Irreversibility.

UNIT - IV: Power Cycles
Power Cycles: Otto, Diesel, Dual Combustion cycles, Sterling Cycle, Atkinson Cycle, Ericcson Cycle, Lenoir Cycle - Description and representation on P-V and T-S diagram, Thermal Efficiency, Mean Effective Pressures on Air standard basis - Comparison of Cycles.

UNIT - V: Pure Substances
Pure Substances: p-v-T- surfaces, T-s and h-s diagrams, Mollier Charts, Phase transformations - Triple point at critical state properties during change of phase, Dryness Fraction - Clausius - Clapeyron Equation Property tables. Mollier charts - Various Thermodynamic processes and energy Transfer - Steam Calorimetry."""
            }
        ]

        # 3. Helper to insert
        def insert_courses(course_list, branch_obj):
            if not branch_obj: return
            print(f"ISeeding courses for {branch_obj.name}...")
            count = 0
            for c in course_list:
                existing = session.query(models.Course).filter(models.Course.code == c["code"]).first()
                if not existing:
                    new_course = models.Course(
                        code=c["code"],
                        title=c["title"],
                        name=c["title"],
                        description=c["desc"],  # Corrected from short_description
                        credits=c["credits"],
                        semester=c["semester"],
                        year_level=(c["semester"] + 1) // 2,
                        branch_id=branch_obj.id,
                        syllabus_text=c["syllabus"],
                        is_active=True
                    )
                    session.add(new_course)
                    count += 1
                else:
                    # Update syllabus if missing
                    if not existing.syllabus_text:
                        existing.syllabus_text = c["syllabus"]
                        print(f"  -> Updated syllabus for {c['code']}")
                    
            print(f"  -> Added {count} new courses.")

        # 4. Execute Insertion
        insert_courses(cse_courses, btech_cse)
        insert_courses(ece_courses, btech_ece)
        insert_courses(me_courses, btech_me)
        
        # Add Generic MTech course
        if mtech_ai:
            mtech_courses = [
                 {
                    "code": "CS501", "title": "Advanced Algorithms", "semester": 1, "credits": 4,
                    "desc": "Advanced graph algorithms, approximation algorithms, and randomized algorithms.",
                    "syllabus": """UNIT - I: Sorting and Graph Algorithms
Review of sorting: Merge sort, Quick sort, Heap sort.
Graph algorithms: BFS, DFS, Topological sort, Strongly connected components.
Single source shortest paths: Bellman-Ford, Dijkstra.
All pairs shortest paths: Floyd-Warshall, Johnson's algorithm.

UNIT - II: Max Flow
Maximum flow: Ford-Fulkerson method, Max-Flow Min-Cut theorem.
Push-relabel algorithms.
Minimum cost flows.

UNIT - III: String Matching and Randomization
String matching: KMP algorithm, Rabin-Karp.
Randomized algorithms: Las Vegas and Monte Carlo algorithms.
Randomized Quicksort, Min-Cut.

UNIT - IV: Approximation Algorithms
NP-completeness and reductions.
Approximation algorithms: Vertex cover, Set cover, TSP.
Approximation schemes (FPTAS).

UNIT - V: Advanced Topics
Amortized analysis.
Online algorithms.
Parallel algorithms."""
                }
            ]
            insert_courses(mtech_courses, mtech_ai)

        session.commit()
        print("Success! Automated course seeding complete.")

    except Exception as e:
        print(f"Error seeding courses: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_courses()
