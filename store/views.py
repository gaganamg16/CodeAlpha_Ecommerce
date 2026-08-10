from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Product, Order, OrderItem


def home(request):
    products = Product.objects.all()
    return render(request, "home.html", {"products": products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "product_detail.html", {"product": product})


def add_to_cart(request, product_id):
    cart = request.session.get("cart", {})
    product_id = str(product_id)

    cart[product_id] = cart.get(product_id, 0) + 1
    request.session["cart"] = cart

    return redirect("cart")


def cart(request):
    cart_data = request.session.get("cart", {})
    products = Product.objects.filter(id__in=cart_data.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart_data[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total": total,
    })


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})
    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session["cart"] = cart
    return redirect("cart")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(request, "Registration successful. Please login.")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")


def checkout(request):
    if not request.user.is_authenticated:
        return redirect("login")

    cart_data = request.session.get("cart", {})

    if not cart_data:
        return redirect("cart")

    products = Product.objects.filter(id__in=cart_data.keys())

    total = 0

    for product in products:
        quantity = cart_data[str(product.id)]
        total += product.price * quantity

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        address = request.POST.get("address")
        phone = request.POST.get("phone")

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            address=address,
            phone=phone,
            total_amount=total
        )

        for product in products:
            quantity = cart_data[str(product.id)]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

            product.stock -= quantity

            if product.stock < 0:
                product.stock = 0

            product.save()

        request.session["cart"] = {}

        return redirect("order_success", order_id=order.id)

    return render(request, "checkout.html", {
        "products": products,
        "total": total
    })


def order_success(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, "order_success.html", {
        "order": order
    })


def orders(request):
    if not request.user.is_authenticated:
        return redirect("login")

    user_orders = Order.objects.filter(
        user=request.user
    ).order_by("-ordered_at")

    return render(request, "orders.html", {
        "orders": user_orders
    })


