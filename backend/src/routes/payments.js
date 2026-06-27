const express = require('express');
const router = express.Router();
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY || 'sk_test_dummy');

const TIER_PRICES = {
  'starter': 19900, // $199.00
  'signature': 59900, // $599.00
  'estate': 250000 // $2,500.00
};

// Create Stripe checkout session
router.post('/checkout', express.json(), async (req, res) => {
  try {
    const { tier, projectId, email } = req.body;
    
    if (!tier || !projectId) {
      return res.status(400).json({ error: 'Tier and projectId are required' });
    }

    const priceAmount = TIER_PRICES[tier.toLowerCase()];
    if (!priceAmount) {
      return res.status(400).json({ error: 'Invalid tier' });
    }

    if (!process.env.STRIPE_SECRET_KEY) {
      // Fallback for development if no key is present
      console.warn('STRIPE_SECRET_KEY not set, using mock checkout');
      return res.json({
        url: `https://checkout.stripe.com/mock?tier=${tier}&projectId=${projectId}`
      });
    }

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      customer_email: email,
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: `Galerie Noire - ${tier.charAt(0).toUpperCase() + tier.slice(1)} Collection`,
              description: `Custom artwork and room transformation for project ${projectId}`,
            },
            unit_amount: priceAmount,
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${process.env.FRONTEND_URL || 'http://localhost:3000'}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.FRONTEND_URL || 'http://localhost:3000'}/cancel`,
      metadata: {
        projectId,
        tier
      }
    });

    res.json({
      id: session.id,
      url: session.url
    });
  } catch (error) {
    console.error('Checkout error:', error);
    res.status(500).json({ error: 'Failed to create checkout session' });
  }
});

// Webhook for payment confirmation
router.post('/webhook', express.raw({type: 'application/json'}), async (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;

  try {
    if (process.env.STRIPE_WEBHOOK_SECRET) {
      event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET);
    } else {
      event = JSON.parse(req.body);
    }
  } catch (err) {
    console.error(`Webhook Error: ${err.message}`);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  // Handle the event
  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    const { projectId, tier } = session.metadata;

    console.log(`Payment confirmed for project ${projectId}, tier ${tier}`);
    
    // Update project status in DB
    const db = require('../utils/db');
    await db.query(
      'UPDATE projects SET status = ? WHERE id = ?',
      ['paid', projectId]
    );
  }

  res.json({received: true});
});

module.exports = router;
