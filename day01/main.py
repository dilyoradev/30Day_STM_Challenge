def add_todos(todos):
    text = input("Enter the todos: ")
    todos.append({"text": text, "done": False})

def list_todos(todos):
    if not todos:
        print("No todos yet.")
        return


    for i, todo in enumerate(todos, start=1):
        status = "[x]" if todo["done"] else "[ ]"
        print(f"{i}. {status} {todo['text']}")

def mark_todos(todos):
    if not todos:
        print("No todos to mark.")

    try:
        user_input = int(input("Enter todo index: "))
    except ValueError:
        print("Please enter a number")
        return
    index = user_input - 1
    if index < 0 or index >= len(todos):
        print("Invalid index.")
        return
    
    todos[index]["done"] = not todos[index]["done"]
    print("Todo updated.")

def main():
    todos = []
    while True:
        print("\n--- Todo App ---")
        print("1. Add todos")
        print("2. List todos")
        print("3. Mark done")
        print("4. Exit")

        choice = input("> ")

        if choice == "1":
            add_todos(todos)
        elif choice == "2":
            list_todos(todos)
        elif choice == "3":
            mark_todos(todos)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()



