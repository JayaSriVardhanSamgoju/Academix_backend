from db import SessionLocal
from models import Course

def seed_syllabus():
    db = SessionLocal()
    try:
        # Get Course 1
        course = db.query(Course).filter(Course.id == 1).first()
        if not course:
            print("Course ID 1 not found. Please create a course first.")
            return

        print(f"Updating syllabus for course: {course.name} ({course.code})")
        
        # Sample Syllabus Text (Data Structures or Generic)
        syllabus = """
        UNIT 1: INTRODUCTION TO ALGORITHMS
        - Algorithm definition, characteristics, and analysis.
        - Asymptotic notations: Big-O, Omega, Theta.
        - Space and Time complexity.
        
        UNIT 2: LINEAR DATA STRUCTURES
        - Arrays: Operations, representation in memory.
        - Linked Lists: Singly, Doubly, Circular linked lists.
        - Stacks: Push, Pop operations, Applications (Infix to Postfix).
        - Queues: Enqueue, Dequeue, Circular Queue, Priority Queue.
        
        UNIT 3: NON-LINEAR DATA STRUCTURES
        - Trees: Binary Trees, BST, AVL Trees, Traversals (Inorder, Preorder, Postorder).
        - Graphs: Representation (Adjacency Matrix/List), BFS, DFS.
        
        UNIT 4: SEARCHING AND SORTING
        - Searching: Linear Search, Binary Search.
        - Sorting: Bubble, Selection, Insertion, Quick, Merge Sort.
        - Hashing: Hash functions, Collision resolution techniques.
        
        UNIT 5: ADVANCED TOPICS
        - Heaps: Min-Max Heap, Heap Sort.
        - B-Trees and B+ Trees basics.
        - Introduction to Dynamic Programming.
        """
        
        course.syllabus_text = syllabus
        db.commit()
        print("Success: Syllabus added to Course 1!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_syllabus()
